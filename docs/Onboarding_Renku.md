# Onboarding project members on Renku
Source: [Renku - Project onboarding](https://renkulab.io/p/renku-team/govtech-hackathon-project-onboarding)

#### Registration on Renku
Click on Login at top right corner of [renkulab.io/](https://renkulab.io). You need a GitHub account.
 
#### Access to your GitHub account from Renku
All the team members, need to follow the [instructions in GitHub integration](https://docs.renkulab.io/en/latest/docs/users/code/guides/connect-renku-account-to-github-or-gitlab-account/) to connect their GitHub account to their Renku account. This is required to commit and push to the team’s repository.
 
#### Data access through Renku for your project
Be mindful that you can add as many data connectors as required. Thus, individual team members can add their personal storage accounts, in case they would like to have their own storage space in their sessions (the rest of the team members will not be able to access others’ individual storage spaces).


#### Weitere Infos
<b style="color:Tomato;">Data</b> can be mounted to the session, but not saved in Renku! Seamless Storage (i.e. Dropbox, Google Drive, Shared Folder on SWITCH drive) is also possible, best used if read + write access are required (since modifications on the mounted data are not stored by default).<br>
<b style="color:Tomato;">Code Repository</b> (GitLab, GitHub), The ".env" is encrypted and the session info also. For security reasons, access and r/w is only managed by Github, not Renku. It is possible to link multiple repositories to the Sessions, also public ones.<br>
<b style="color:Tomato;">Compute session</b> launch on SCSC Compute Clusters, but one can also connect their own infrastructure. In terms of GPU support: NVIDIA A100 20GB GPU’s are available. Reproducable Environment (environment.yml, requirements.txt, renv.lock files) can be preloaded and made available for users.<br>

<https://docs.renkulab.io/en/latest/docs/users/getting-started/><br>
