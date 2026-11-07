# opencode-kit
#
# Agents for OpenCode, each with the skills, commands and scripts it needs.
# 'make install' asks which agents, skills and MCP servers to wire into
# ~/.config/opencode (all of them by default): agents, commands and libs become
# links there, and skills and MCP servers go into your OpenCode config.

OPENCODE_DIR ?= $(HOME)/.config/opencode
MODE         ?= link
PYTHON       ?= python3
AGENTS       ?=
SKILLS       ?=
MCP          ?=
REPO         := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

.DEFAULT_GOAL := help
.PHONY: help install uninstall deps check test skills-add skills-remove

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "; print "Targets:"} /^[a-z-]+:.*## / {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo
	@echo "Agents: $$(cd $(REPO) && ls agents/*.md 2>/dev/null | xargs -n1 basename | sed 's/\.md$$//' | tr '\n' ' ')"
	@echo "Skip the checklist: make install AGENTS='designer grill' SKILLS=all MCP=flux (names, all or none)"

install: ## Choose agents, skills and MCP servers (all by default), then wire them in
	@sel=$$(mktemp) && trap 'rm -f "$$sel"' EXIT && \
	$(PYTHON) "$(REPO)/scripts/kit.py" select "$(OPENCODE_DIR)" "$(REPO)" "$$sel" "$(AGENTS)" "$(SKILLS)" "$(MCP)" && \
	if [ -s "$$sel" ]; then \
		bash "$(REPO)/scripts/wire.sh" install "$(OPENCODE_DIR)" "$(REPO)" "$(MODE)" "$$sel" && \
		$(PYTHON) "$(REPO)/scripts/opencode-config.py" sync "$(OPENCODE_DIR)" "$(REPO)" "$$sel" && \
		echo "Done. Run 'make check', then open a new session."; \
	fi

uninstall: ## Remove everything the kit installed, restoring any backups
	@$(PYTHON) "$(REPO)/scripts/opencode-config.py" remove "$(OPENCODE_DIR)" "$(REPO)"
	@bash "$(REPO)/scripts/wire.sh" uninstall "$(OPENCODE_DIR)" "$(REPO)"

skills-add: ## Register every skill, as the whole skills directory, in your config
	@$(PYTHON) "$(REPO)/scripts/opencode-config.py" skills-add "$(OPENCODE_DIR)" "$(REPO)"

skills-remove: ## Remove every entry for this repo's skills from your config
	@$(PYTHON) "$(REPO)/scripts/opencode-config.py" skills-remove "$(OPENCODE_DIR)" "$(REPO)"

deps: ## Install node dependencies for every installed lib that has a package.json
	@for d in "$(REPO)"/lib/*/; do \
		[ -f "$$d/package.json" ] || continue; \
		name=$$(basename "$$d"); \
		if [ ! -e "$(OPENCODE_DIR)/lib/$$name" ]; then echo "skip  $$name (not installed)"; continue; fi; \
		echo "== $$name"; \
		(cd "$$d" && npm install --no-fund --no-audit); \
		if grep -q '"playwright"' "$$d/package.json"; then \
			(cd "$$d" && ./node_modules/.bin/playwright install chromium); \
		fi; \
	done

check: ## Verify the install: links, libs, dependencies, skills entries
	@$(PYTHON) "$(REPO)/scripts/kit.py" check "$(OPENCODE_DIR)" "$(REPO)"

test: ## Render a sample artifact through the design verify script
	@script="$(OPENCODE_DIR)/lib/design/verify.mjs"; \
	if [ ! -f "$$script" ]; then echo "no design verify script installed (run make install)"; exit 1; fi; \
	tmp=$$(mktemp -d); \
	printf '%s\n' '<!doctype html><title>t</title><h1>ok</h1><p style="font:16px/1.5 sans-serif">sample</p>' > "$$tmp/sample.html"; \
	node "$$script" "$$tmp/sample.html" --out "$$tmp/out.png" --quiet; \
	echo "screenshot: $$tmp/out.png"
