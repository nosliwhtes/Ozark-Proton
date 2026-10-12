# Disabled Wine patches

`multi-process-launcher-x11-fallback.patch` is retained for provenance and is
not applied by protonprep. Wine-Wayland now renders launcher windows from
other processes directly. Restore this patch only with a deliberate change
to the active preparation sequence.

The older disabled EM, media, controller and offscreen-rendering imports were
removed in the upstream component refresh. Their original files and exclusion
notes remain in Git history at Ozark commit
`b5293279b3fedecde659c4486592a26f0992bf7b`. Their removal does not enable them.
See `../wine-wayland/README.md` for the active import and rebase history.
