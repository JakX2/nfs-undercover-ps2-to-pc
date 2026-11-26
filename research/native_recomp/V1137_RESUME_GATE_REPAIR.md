# V1137: repair V1136 owner launcher regression

V1136 accidentally expanded the suffix of the shell script during a text replacement, breaking bash syntax and preventing private execution. Restore the known-good V1135 script and insert the three ordered-marker checks by line, plus the per-mode census. The V1136 C++ integration gate independently passed; private execution must rerun. No original resume instruction or continuous boot is claimed.
