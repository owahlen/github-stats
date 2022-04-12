# Create statistics about the github account of an organization
This repository contains scripts that create statistics for an organization that is using Github.
It is assumed that SAML is used to give the organization's employees access.

## Setup
A [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
needs to be created that is authorized to be used with the organization.
The permission scope of this token needs to be `repo`, `admin:org` and `user`.

The scripts read the configuration file `github.ini`.
It contains this token and the name of the organization.
The file `github.ini.example` can be used as reference to understand the syntax.

## create-user-prs.py
This script fetches all users that are part of the organization and that were authenticated via SAML.
For each user it counts the number of pull requests in each of the last 12 months
and writes the result into the file `user-prs.json`.

## prs2xlsx.py
This script reads the file `user-prs.json` and converts it into an Excel spreadsheet
called `prs.xlsx`.
