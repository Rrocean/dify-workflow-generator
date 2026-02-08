import * as vscode from 'vscode';
import * as yaml from 'js-yaml';

export class WorkflowPreviewProvider implements vscode.WebviewPanelSerializer {
    private _panel?: vscode.WebviewPanel;

    constructor(private readonly _extensionUri: vscode.Uri) {}

    async resolveWebviewPanel(
        webviewPanel: vscode.WebviewPanel,
        state: unknown
    ): Promise<void> {
        this._panel = webviewPanel;
        this._panel.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };
    }

    showPreview(content: string, filename: string) {
        if (this._panel) {
            this._panel.reveal(vscode.ViewColumn.Two);
        } else {
            this._panel = vscode.window.createWebviewPanel(
                'difyWorkflowPreview',
                `Preview: ${filename}`,
                vscode.ViewColumn.Two,
                {
                    enableScripts: true,
                    retainContextWhenHidden: true
                }
            );

            this._panel.onDidDispose(() => {
                this._panel = undefined;
            });
        }

        this._panel.webview.html = this._getHtml(content);
    }

    private _getHtml(content: string): string {
        let workflow;
        try {
            workflow = yaml.load(content) as any;
        } catch (e) {
            return `<!DOCTYPE html>
                <html>
                <body>
                    <h2 style="color: #e74c3c;">Invalid Workflow</h2>
                    <pre>${e}</pre>
                </body>
                </html>`;
        }

        const nodes = workflow?.workflow?.graph?.nodes || [];
        const edges = workflow?.workflow?.graph?.edges || [];

        // Generate Mermaid diagram
        const mermaidDiagram = this._generateMermaid(nodes, edges);

        return `<!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        padding: 20px;
                        background: #f5f5f5;
                    }
                    .header {
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        margin-bottom: 20px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .header h1 {
                        margin: 0 0 10px 0;
                        color: #333;
                    }
                    .meta {
                        color: #666;
                        font-size: 14px;
                    }
                    .diagram {
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .stats {
                        display: flex;
                        gap: 20px;
                        margin-top: 15px;
                    }
                    .stat {
                        background: #f0f0f0;
                        padding: 10px 15px;
                        border-radius: 4px;
                    }
                    .stat-label {
                        font-size: 12px;
                        color: #666;
                    }
                    .stat-value {
                        font-size: 20px;
                        font-weight: bold;
                        color: #333;
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>${workflow?.app?.name || 'Untitled Workflow'}</h1>
                    <div class="meta">
                        <p>Mode: ${workflow?.app?.mode || 'unknown'}</p>
                        <p>${workflow?.app?.description || 'No description'}</p>
                    </div>
                    <div class="stats">
                        <div class="stat">
                            <div class="stat-label">Nodes</div>
                            <div class="stat-value">${nodes.length}</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Edges</div>
                            <div class="stat-value">${edges.length}</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">DSL Version</div>
                            <div class="stat-value">${workflow?.version || 'unknown'}</div>
                        </div>
                    </div>
                </div>
                <div class="diagram">
                    <h3>Workflow Diagram</h3>
                    <div class="mermaid">
${mermaidDiagram}
                    </div>
                </div>
                <script>
                    mermaid.initialize({
                        startOnLoad: true,
                        theme: 'default',
                        flowchart: {
                            useMaxWidth: true,
                            htmlLabels: true
                        }
                    });
                </script>
            </body>
            </html>`;
    }

    private _generateMermaid(nodes: any[], edges: any[]): string {
        if (!nodes.length) return 'flowchart TD\n    A[No nodes]';

        let diagram = 'flowchart TD\n';

        // Add nodes with styling
        nodes.forEach((node, index) => {
            const id = `N${index}`;
            const type = node.data?.type || 'unknown';
            const title = node.data?.title || type;

            // Style based on node type
            let shape = '([{}])';
            let className = '';

            switch (type) {
                case 'start':
                    shape = '(({}))';
                    className = 'classDef start fill:#e1f5fe,stroke:#01579b';
                    break;
                case 'end':
                    shape = '(({}))';
                    className = 'classDef end fill:#fce4ec,stroke:#880e4f';
                    break;
                case 'llm':
                    shape = '[{}]';
                    className = 'classDef llm fill:#f3e5f5,stroke:#4a148c';
                    break;
                case 'http':
                    shape = '[{}]';
                    className = 'classDef http fill:#e8f5e9,stroke:#1b5e20';
                    break;
                case 'if-else':
                    shape = '{{}}';
                    className = 'classDef ifelse fill:#fff3e0,stroke:#e65100';
                    break;
                default:
                    shape = '[{}]';
            }

            const shapeStart = shape[0];
            const shapeEnd = shape[shape.length - 1];
            diagram += `    ${id}${shapeStart}"${title}"${shapeEnd}\n`;
        });

        // Add edges
        edges.forEach((edge, index) => {
            const sourceIndex = nodes.findIndex(n => n.id === edge.source || n.data?.id === edge.source);
            const targetIndex = nodes.findIndex(n => n.id === edge.target || n.data?.id === edge.target);

            if (sourceIndex >= 0 && targetIndex >= 0) {
                const label = edge.sourceHandle ? `|${edge.sourceHandle}|` : '';
                diagram += `    N${sourceIndex} -->${label} N${targetIndex}\n`;
            }
        });

        return diagram;
    }
}
