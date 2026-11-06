# opencode-designer — install the designer agent, skills and command into OpenCode.
#
# Wired into ~/.config/opencode by default; override OPENCODE_DIR for a test tree.

OPENCODE_DIR ?= $(HOME)/.config/opencode
MODE         ?= link
PYTHON       ?= python3
REPO         := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
BACKUP       := .bak.$(shell date +%Y%m%d-%H%M%S)

.DEFAULT_GOAL := help
.PHONY: help install uninstall deps check test skills-add skills-remove

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "; print "Targets:"} /^[a-z-]+:.*## / {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Link the agent, command and verify script, then register the skills path
	@mkdir -p "$(OPENCODE_DIR)/agents" "$(OPENCODE_DIR)/commands" "$(OPENCODE_DIR)/lib"
	@$(call place_file,$(REPO)/agents/designer.md,$(OPENCODE_DIR)/agents/designer.md)
	@$(call place_file,$(REPO)/commands/design.md,$(OPENCODE_DIR)/commands/design.md)
	@$(call place_dir,$(REPO)/lib/design,$(OPENCODE_DIR)/lib/design)
	@$(MAKE) --no-print-directory -s skills-add
	@echo "Done. Run 'make check' to verify, then open a new session and try /design."

uninstall: ## Remove the links and the skills entry, restoring any *.bak.* backups
	@$(MAKE) --no-print-directory -s skills-remove
	@for t in "$(OPENCODE_DIR)/agents/designer.md" "$(OPENCODE_DIR)/commands/design.md" "$(OPENCODE_DIR)/lib/design"; do \
		if [ -L "$$t" ]; then rm -f "$$t"; echo "removed link $$t"; fi; \
		b=$$(ls -d "$$t".bak.* 2>/dev/null | tail -1); \
		if [ -n "$$b" ]; then mv "$$b" "$$t"; echo "restored $$t from $$b"; fi; \
	done

skills-add: ## Add the repo skills directory to the 'skills' array in your OpenCode config
	@$(PYTHON) "$(REPO)/scripts/skills-config.py" add "$(OPENCODE_DIR)" "$(REPO)/skills"

skills-remove: ## Remove the repo skills directory from your OpenCode config
	@$(PYTHON) "$(REPO)/scripts/skills-config.py" remove "$(OPENCODE_DIR)" "$(REPO)/skills"

deps: ## Install playwright and headless chromium for verify.mjs (~190 MB, one time)
	@cd "$(REPO)/lib/design" && npm install --no-fund --no-audit
	@cd "$(REPO)/lib/design" && ./node_modules/.bin/playwright install chromium

check: ## Verify the install: links, config entry, playwright
	@fail=0; \
	for t in "agents/designer.md" "commands/design.md" "lib/design/verify.mjs"; do \
		if [ -r "$(OPENCODE_DIR)/$$t" ]; then echo "ok    $(OPENCODE_DIR)/$$t"; \
		else echo "MISS  $(OPENCODE_DIR)/$$t (run make install)"; fail=1; fi; \
	done; \
	if $(PYTHON) "$(REPO)/scripts/skills-config.py" check "$(OPENCODE_DIR)" "$(REPO)/skills" >/dev/null 2>&1; then \
		echo "ok    skills entry in $(OPENCODE_DIR)"; \
	else echo "MISS  skills entry in $(OPENCODE_DIR) (run make skills-add)"; fail=1; fi; \
	if (cd "$(REPO)/lib/design" && node -e "import('playwright').then(()=>0)" >/dev/null 2>&1); then \
		echo "ok    playwright in lib/design"; \
	else echo "MISS  playwright in lib/design (run make deps)"; fail=1; fi; \
	exit $$fail

test: ## Render a sample artifact through the verify script
	@tmp=$$(mktemp -d); printf '%s\n' '<!doctype html><title>t</title><h1>ok</h1><p style="font:16px/1.5 sans-serif">sample</p>' > "$$tmp/sample.html"; \
	node "$(OPENCODE_DIR)/lib/design/verify.mjs" "$$tmp/sample.html" --out "$$tmp/out.png" --quiet; \
	echo "screenshot: $$tmp/out.png"

# place_file <src> <dest>: symlink (default) or copy, backing up a real file first.
define place_file
target="$(2)"; src="$(1)"; \
if [ "$(MODE)" = "copy" ]; then \
	if [ -e "$$target" ] && [ ! -L "$$target" ]; then mv "$$target" "$$target$(BACKUP)"; echo "backed up $$target"; fi; \
	rm -f "$$target"; cp "$$src" "$$target"; echo "copied $$target"; \
else \
	if [ -e "$$target" ] && [ ! -L "$$target" ]; then mv "$$target" "$$target$(BACKUP)"; echo "backed up $$target"; fi; \
	rm -f "$$target"; ln -s "$$src" "$$target"; echo "linked $$target -> $$src"; \
fi
endef

# place_dir <src> <dest>: always a symlink, so verify.mjs resolves its node_modules.
define place_dir
target="$(2)"; src="$(1)"; \
if [ -e "$$target" ] && [ ! -L "$$target" ]; then mv "$$target" "$$target$(BACKUP)"; echo "backed up $$target"; fi; \
rm -rf "$$target"; ln -s "$$src" "$$target"; echo "linked $$target -> $$src"
endef
