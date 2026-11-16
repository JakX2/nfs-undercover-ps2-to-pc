// Source-only Ghidra headless script. Exports addresses/call edges, never code bytes.
// Synthetic mode is ONLY for the independently authored CI DOL.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Set;
import java.util.TreeSet;

public class ExportWiiFunctionManifest extends GhidraScript {
    private static final String LANGUAGE = "PowerPC:BE:32:Gekko_Broadway";

    private static String hex(long value) {
        return String.format("0x%08X", value);
    }

    private void seedSynthetic() throws Exception {
        long[] entries = {0x8000403CL, 0x80004050L};
        String[] names = {"synthetic_start", "synthetic_helper"};
        FunctionManager manager = currentProgram.getFunctionManager();
        for (int i = 0; i < entries.length; ++i) {
            Address entry = toAddr(entries[i]);
            if (!currentProgram.getMemory().contains(entry)) {
                throw new IllegalStateException("Synthetic DOL not mapped at expected guest address");
            }
            if (manager.getFunctionAt(entry) == null) {
                disassemble(entry);
                if (createFunction(entry, names[i]) == null) {
                    throw new IllegalStateException("Could not seed synthetic function");
                }
            }
        }
        analyzeChanges(currentProgram);
    }

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2 || currentProgram == null || !isRunningHeadless()) {
            throw new IllegalArgumentException("Expected: OUTPUT_JSON synthetic|private (headless only)");
        }
        boolean synthetic = args[1].equals("synthetic");
        if (!synthetic && !args[1].equals("private")) {
            throw new IllegalArgumentException("Unsupported mode");
        }
        String lang = currentProgram.getLanguageID().toString();
        if (!LANGUAGE.equals(lang)) {
            throw new IllegalStateException("Incorrect loader or Wii language: " + lang);
        }
        if (synthetic) {
            seedSynthetic();
        }

        FunctionManager manager = currentProgram.getFunctionManager();
        StringBuilder json = new StringBuilder();
        json.append("{\"schema\":\"uc-wii-function-index-v1\",\"language\":\"")
            .append(LANGUAGE).append("\",\"functions\":[");
        long count = 0;
        for (Function function : manager.getFunctions(true)) {
            if (count > 0) {
                json.append(',');
            }
            json.append("{\"pc\":\"").append(hex(function.getEntryPoint().getOffset()));
            json.append("\",\"size\":").append(function.getBody().getNumAddresses());
            json.append(",\"calls\":[");
            Set<Long> targets = new TreeSet<>();
            for (Function called : function.getCalledFunctions(monitor)) {
                targets.add(called.getEntryPoint().getOffset());
            }
            boolean first = true;
            for (long target : targets) {
                if (!first) {
                    json.append(',');
                }
                json.append('"').append(hex(target)).append('"');
                first = false;
            }
            json.append("]}");
            ++count;
        }
        json.append("]}\n");
        if (count == 0) {
            throw new IllegalStateException("No discovered native Wii functions");
        }

        // Refuse to publish a function list to an existing filesystem target.
        Path output = Path.of(args[0]);
        if (Files.exists(output)) {
            throw new IllegalStateException("Refusing to overwrite existing function manifest");
        }
        Files.writeString(output, json.toString(), StandardCharsets.UTF_8);
        println("PASS: Ghidra Wii native-language functions=" + count + " (no code bytes exported)");
    }
}
