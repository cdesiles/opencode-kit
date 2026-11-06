# opencode-kit
#
# Agents for OpenCode, each with the skills, commands and scripts it needs.
# Every file in agents/, commands/ and lib/ is wired into ~/.config/opencode;
# skills/ is registered once through the 'skills' array in your OpenCode config.

OPENCODE_DIR ?= $(HOME)/.config/opencode
MODE         ?= link
PYTHON       ?= python3
REPO         := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

.DEFAULT_GOAL := help
.PHONY: help install uninstall deps check test skills-add skills-remove

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "; print "Targets:"} /^[a-z-]+:.*## / {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo
	@echo "Agents: $$(cd $(REPO) && ls agents/*.md 2>/dev/null | xargs -n1 basename | sed 's/\.md$$//' | tr '\n' ' ')"

install: ## Link every agent, command and lib, then register the skills path
	@bash "$(REPO)/scripts/wire.sh" install "$(OPENCODE_DIR)" "$(REPO)" "$(MODE)"
	@$(MAKE) --no-print-directory -s skills-add
	@echo "Done. Run 'make check', then open a new session."

uninstall: ## Remove the links and the skills entry, restoring any backups
	@$(MAKE) --no-print-directory -s skills-remove
	@bash "$(REPO)/scripts/wire.sh" uninstall "$(OPENCODE_DIR)" "$(REPO)"

skills-add: ## Add this repo's skills directory to the 'skills' array in your config
	@$(PYTHON) "$(REPO)/scripts/skills-config.py" add "$(OPENCODE_DIR)" "$(REPO)/skills"

skills-remove: ## Remove this repo's skills directory from your config
	@$(PYTHON) "$(REPO)/scripts/skills-config.py" remove "$(OPENCODE_DIR)" "$(REPO)/skills"

deps: ## Install node dependencies for every lib/*/ that has a package.json
	@for d in "$(REPO)"/lib/*/; do \
		[ -f "$$d/package.json" ] || continue; \
		echo "== $$(basename "$$d")"; \
		(cd "$$d" && npm install --no-fund --no-audit); \
		if grep -q '"playwright"' "$$d/package.json"; then \
			(cd "$$d" && ./node_modules/.bin/playwright install chromium); \
		fi; \
	done

check: ## Verify the install: links, config entry, dependencies
	@fail=0; \
	for f in $(REPO)/agents/*.md $(REPO)/commands/*.md; do \
		[ -e "$$f" ] || continue; \
		kind=$$(basename $$(dirname "$$f")); dest="$(OPENCODE_DIR)/$$kind/$$(basename "$$f")"; \
		if [ -r "$$dest" ]; then echo "ok    $$dest"; else echo "MISS  $$dest (run make install)"; fail=1; fi; \
	done; \
	for d in "$(REPO)"/lib/*/; do \
		[ -d "$$d" ] || continue; name=$$(basename "$$d"); \
		if [ -r "$(OPENCODE_DIR)/lib/$$name" ]; then echo "ok    $(OPENCODE_DIR)/lib/$$name"; \
		else echo "MISS  $(OPENCODE_DIR)/lib/$$name (run make install)"; fail=1; fi; \
		if [ -f "$$d/package.json" ] && [ ! -d "$$d/node_modules" ]; then \
			echo "MISS  $$name dependencies (run make deps)"; fail=1; \
		fi; \
	done; \
	if $(PYTHON) "$(REPO)/scripts/skills-config.py" check "$(OPENCODE_DIR)" "$(REPO)/skills" >/dev/null 2>&1; then \
		echo "ok    skills entry in $(OPENCODE_DIR)"; \
	else echo "MISS  skills entry in $(OPENCODE_DIR) (run make skills-add)"; fail=1; fi; \
	exit $$fail

test: ## Render a sample artifact through the design verify script
	@script="$(OPENCODE_DIR)/lib/design/verify.mjs"; \
	if [ ! -f "$$script" ]; then echo "no design verify script installed (run make install)"; exit 1; fi; \
	tmp=$$(mktemp -d); \
	printf '%s\n' '<!doctype html><title>t</title><h1>ok</h1><p style="font:16px/1.5 sans-serif">sample</p>' > "$$tmp/sample.html"; \
	node "$$script" "$$tmp/sample.html" --out "$$tmp/out.png" --quiet; \
	echo "screenshot: $$tmp/out.png"
