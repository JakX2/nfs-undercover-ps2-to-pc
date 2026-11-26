# V1061: preserve legacy modes and require real owner jobs

Restrict the new return-mode suffix parser to the error-queue namespace; otherwise existing callback-return and handler-return would incorrectly enter the new parser. Also fail closed when a successful historical workflow skipped the private owner job: require exactly one matching owner job, completed with success. The V1059 workflow remains manual and undispatched. No original execution claim.
