# V1080: exact third-dispatch census and const saved-frame access

V1076 owner run 45747287759 passed all 32 original third dispatcher trials: 153 visits, five entries, two PI reads, ten polls, 38 saved fields, zero fallback. Require that exact census in the owner runner. V1078 integration run 45747754689 failed compilation because the new const frame check called a non-const capture accessor. Add the const overload rather than casting away const or relaxing frame validation. V1079/V1080 ACK tests still pending. The full-image continuous build remains separate.
