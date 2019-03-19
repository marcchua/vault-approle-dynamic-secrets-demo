# Vault AppRole Example using Python 

This example provides a simple python script that demonstrate authentication process of using Vault’s AppRole Auth method to read in the ROLE-ID and the SECRET-ID from two different sources.  We then cover policy attached to the role than allows read access to to a dynamic database secrets backend (with specified ttl) and reads in a Postgres DB secret for the app the to use.

We also all a loop in a try block that throws an exception if the following conditions returns true:

1. AppRole Auth token expired and needs to be recreated/renewed

2. Database Secrets token have expired and needs to be recreated/renewed


