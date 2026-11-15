# Validation scope

The integration validator checks skill frontmatter and names, canonical local references and discovery wrappers, required agent bridges, retained source licenses, pinned source revisions and snapshot file hashes. It does not execute upstream code or contact model providers.

Run from the workspace root:

```sh
python3 tooling/scripts/validate_agentic_skills.py
```

After opening the repository in VS Code, start a new agent chat and check whether the intended extension lists the workspace skills. Ask it to identify the relevant canonical file for a test-first, debugging, or review task. Then test one small real task using the same acceptance criteria as a baseline run. Record task quality, corrections, elapsed time, and available token/cost evidence.

File validation does not establish skill discovery in every extension, model obedience, third-party runtime compatibility, security-audit isolation, or a measured productivity gain. Full upstream plugin behavior and automatic hooks were not installed. No application-framework dependencies were added.
