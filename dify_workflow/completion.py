"""
Shell completion for CLI
Generates completion scripts for Bash, Zsh, and Fish
"""
from typing import List


BASH_COMPLETION = """
_dify_workflow_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Main commands
    local commands="interactive i chat c import ai build b validate v visualize viz template tpl analyze a diff d docs profile help"

    case "${COMP_CWORD}" in
        1)
            COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
            return 0
            ;;
        *)
            case "${COMP_WORDS[1]}" in
                template|tpl)
                    case "${prev}" in
                        template|tpl)
                            COMPREPLY=( $(compgen -W "list create" -- ${cur}) )
                            ;;
                        create)
                            COMPREPLY=( $(compgen -W "translation chatbot summarizer code-reviewer article-generator" -- ${cur}) )
                            ;;
                        -o|--output)
                            COMPREPLY=( $(compgen -f -- ${cur}) )
                            ;;
                        *)
                            COMPREPLY=( $(compgen -W "-o --output" -- ${cur}) )
                            ;;
                    esac
                    ;;
                build|b)
                    COMPREPLY=( $(compgen -f -- ${cur}) )
                    ;;
                validate|v|visualize|viz|analyze|a|profile)
                    COMPREPLY=( $(compgen -f -X '!*.yml' -- ${cur}) )
                    ;;
                interactive|i)
                    COMPREPLY=( $(compgen -W "--lang" -- ${cur}) )
                    ;;
                *)
                    COMPREPLY=( $(compgen -f -- ${cur}) )
                    ;;
            esac
            ;;
    esac
}

complete -F _dify_workflow_completion dify-workflow
"""


ZSH_COMPLETION = """
#compdef dify-workflow

_dify-workflow() {
    local curcontext="$curcontext" state line
    typeset -A opt_args

    _arguments -C \\
        '1: :_dify_workflow_commands' \\
        '*:: :->args'

    case "$line[1]" in
        template|tpl)
            _dify_workflow_template
            ;;
        build|b)
            _arguments \\
                '-o[Output file]:output:_files' \\
                '*:input:_files -g "*.py"'
            ;;
        validate|v|visualize|viz|analyze|a|profile)
            _arguments '*:workflow:_files -g "*.yml"'
            ;;
        diff|d)
            _arguments \\
                '*:workflows:_files -g "*.yml"'
            ;;
    esac
}

_dify_workflow_commands() {
    local commands=(
        'interactive:Interactive workflow builder'
        'chat:AI chat mode'
        'build:Build workflow from Python'
        'validate:Validate workflow'
        'visualize:Visualize workflow'
        'template:Use templates'
        'analyze:Analyze workflow'
        'diff:Compare workflows'
        'docs:Generate documentation'
        'profile:Profile performance'
        'import:Convert YAML to Python'
        'ai:AI-powered creation'
        'help:Show help'
    )
    _describe -t commands 'dify-workflow commands' commands
}

_dify_workflow_template() {
    local curcontext="$curcontext"

    _arguments -C \\
        '1: :_dify_template_actions' \\
        '*:: :->args'

    case "$line[1]" in
        create)
            _arguments \\
                ':template:_dify_templates' \\
                '-o[Output file]:output:_files'
            ;;
    esac
}

_dify_template_actions() {
    local actions=(
        'list:List available templates'
        'create:Create from template'
    )
    _describe -t actions 'template actions' actions
}

_dify_templates() {
    local templates=(
        'translation:Text translation'
        'chatbot:AI chatbot'
        'summarizer:Text summarization'
        'code-reviewer:Code review'
        'article-generator:Article generation'
        'rag-chat:RAG chat'
        'sentiment-analyzer:Sentiment analysis'
        'qa-bot:Question answering'
        'email-writer:Email composition'
    )
    _describe -t templates 'templates' templates
}

compdef _dify-workflow dify-workflow
"""


FISH_COMPLETION = """
function __dify_workflow_commands
    echo "interactive\tInteractive workflow builder"
    echo "chat\tAI chat mode"
    echo "build\tBuild from Python"
    echo "validate\tValidate workflow"
    echo "visualize\tVisualize workflow"
    echo "template\tUse templates"
    echo "analyze\tAnalyze workflow"
    echo "diff\tCompare workflows"
    echo "docs\tGenerate docs"
    echo "profile\tProfile performance"
    echo "import\tConvert to Python"
    echo "ai\tAI creation"
    echo "help\tShow help"
end

function __dify_templates
    echo "translation\tText translation"
    echo "chatbot\tAI chatbot"
    echo "summarizer\tText summarization"
    echo "code-reviewer\tCode review"
    echo "article-generator\tArticle generation"
end

complete -c dify-workflow -f
complete -c dify-workflow -n "__fish_use_subcommand" -a "(__dify_workflow_commands)"
complete -c dify-workflow -n "__fish_seen_subcommand_from template tpl" -a "list create"
complete -c dify-workflow -n "__fish_seen_subcommand_from create" -a "(__dify_templates)"
complete -c dify-workflow -n "__fish_seen_subcommand_from validate visualize analyze profile" -a "(__fish_complete_suffix .yml)"
complete -c dify-workflow -n "__fish_seen_subcommand_from build" -a "(__fish_complete_suffix .py)"
"""


def install_completion(shell: str = "bash") -> str:
    """
    Get completion script for specified shell

    Args:
        shell: One of 'bash', 'zsh', 'fish'

    Returns:
        Completion script as string
    """
    if shell == "bash":
        return BASH_COMPLETION
    elif shell == "zsh":
        return ZSH_COMPLETION
    elif shell == "fish":
        return FISH_COMPLETION
    else:
        raise ValueError(f"Unsupported shell: {shell}")


def get_install_path(shell: str) -> str:
    """Get recommended installation path for completion script"""
    import os

    if shell == "bash":
        return os.path.expanduser("~/.bash_completion.d/dify-workflow")
    elif shell == "zsh":
        return os.path.expanduser("~/.zsh/completions/_dify-workflow")
    elif shell == "fish":
        return os.path.expanduser("~/.config/fish/completions/dify-workflow.fish")
    else:
        raise ValueError(f"Unsupported shell: {shell}")


# Instructions for manual installation
INSTALL_INSTRUCTIONS = """
Shell Completion Installation
=============================

Bash:
-----
# Save completion script
mkdir -p ~/.bash_completion.d
dify-workflow completion bash > ~/.bash_completion.d/dify-workflow

# Add to ~/.bashrc
[ -f ~/.bash_completion.d/dify-workflow ] && source ~/.bash_completion.d/dify-workflow

# Or use system-wide
sudo dify-workflow completion bash > /etc/bash_completion.d/dify-workflow

Zsh:
----
# Save completion script
mkdir -p ~/.zsh/completions
dify-workflow completion zsh > ~/.zsh/completions/_dify-workflow

# Add to ~/.zshrc
fpath=(~/.zsh/completions $fpath)
autoload -U compinit && compinit

Fish:
-----
# Save completion script
mkdir -p ~/.config/fish/completions
dify-workflow completion fish > ~/.config/fish/completions/dify-workflow.fish

# Fish completions are loaded automatically
"""
