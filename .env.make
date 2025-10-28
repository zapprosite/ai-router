## Optional overrides for constrained/rootless environments
# empty SUDO disables privileged calls in Makefile recipes
SUDO=

# example: redirect backups to Desktop with timestamp (uses Makefile STAMP)
BACKUP_DIR ?= $(HOME)/Desktop/AI-Router-Backup-$(STAMP)

