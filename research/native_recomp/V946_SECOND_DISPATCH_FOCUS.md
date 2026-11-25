# V946: focused original second dispatcher

V932 full-image owner run 45711850472 passed continuous original scheduler/loader/RFI and second external exception entry (86 visits, Linux x64 complete image linked). V945 source-only run 45714330330 passed 17 second-dispatch cases, 13 first-dispatch cases, 22 RFI cases.

V946 privately authenticates the original dispatcher, scheduler-disable and three original OS leaves, retaining the original indirect handler call. Explicit non-selected control paths and post-indirect continuation are refusal guards. The fixture starts with a prepared saved integer frame and a second actual backend SI completion, with PI MMIO reads from the real fixture bus. Stops at original handler entry before any handler instruction. Split/nonsplit execution, negative PI/frame controls pending. This fixture does not claim continuous startup or a second ACK.
