import * as vscode from 'vscode';
import * as yaml from 'js-yaml';
import axios from 'axios';
import { WorkflowPreviewProvider } from './preview';

export function activate(context: vscode.ExtensionContext) {
    console.log('Dify Workflow extension is now active');

    // Register preview provider
    const previewProvider = new WorkflowPreviewProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewPanelProvider('difyWorkflowPreview', previewProvider)
    );

    // Preview command
    let previewCommand = vscode.commands.registerCommand('dify.preview', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        const document = editor.document;
        const content = document.getText();

        try {
            // Validate YAML
            yaml.load(content);

            // Show preview
            previewProvider.showPreview(content, document.fileName);
        } catch (e) {
            vscode.window.showErrorMessage(`Invalid YAML: ${e}`);
        }
    });

    // Validate command
    let validateCommand = vscode.commands.registerCommand('dify.validate', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        const content = editor.document.getText();
        const config = vscode.workspace.getConfiguration('dify');
        const apiUrl = config.get<string>('apiUrl', 'http://localhost:8765');

        try {
            // Send to API for validation
            const response = await axios.post(`${apiUrl}/api/validate`, {
                workflow: content
            });

            if (response.data.valid) {
                vscode.window.showInformationMessage('✓ Workflow is valid');
            } else {
                vscode.window.showWarningMessage(`Workflow has issues: ${response.data.issues?.join(', ')}`);
            }
        } catch (e) {
            vscode.window.showErrorMessage(`Validation failed: ${e}`);
        }
    });

    // Visualize command
    let visualizeCommand = vscode.commands.registerCommand('dify.visualize', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        const content = editor.document.getText();
        const config = vscode.workspace.getConfiguration('dify');
        const apiUrl = config.get<string>('apiUrl', 'http://localhost:8765');

        try {
            const response = await axios.post(`${apiUrl}/api/visualize`, {
                workflow: content,
                format: 'mermaid'
            });

            // Create new document with visualization
            const doc = await vscode.workspace.openTextDocument({
                content: response.data.visualization,
                language: 'markdown'
            });
            await vscode.window.showTextDocument(doc);
        } catch (e) {
            vscode.window.showErrorMessage(`Visualization failed: ${e}`);
        }
    });

    // Export to Python command
    let exportPythonCommand = vscode.commands.registerCommand('dify.exportPython', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        const content = editor.document.getText();
        const config = vscode.workspace.getConfiguration('dify');
        const apiUrl = config.get<string>('apiUrl', 'http://localhost:8765');

        try {
            const response = await axios.post(`${apiUrl}/api/import`, {
                workflow: content,
                format: 'python'
            });

            // Create new document with Python code
            const doc = await vscode.workspace.openTextDocument({
                content: response.data.code,
                language: 'python'
            });
            await vscode.window.showTextDocument(doc);
        } catch (e) {
            vscode.window.showErrorMessage(`Export failed: ${e}`);
        }
    });

    // Deploy command
    let deployCommand = vscode.commands.registerCommand('dify.deploy', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        const content = editor.document.getText();

        // Get deployment configuration
        const deployUrl = await vscode.window.showInputBox({
            prompt: 'Enter Dify deployment URL',
            value: 'http://localhost'
        });

        if (!deployUrl) return;

        const apiKey = await vscode.window.showInputBox({
            prompt: 'Enter API key',
            password: true
        });

        try {
            // Deploy to Dify
            await axios.post(`${deployUrl}/v1/workflows`, {
                workflow: content
            }, {
                headers: {
                    'Authorization': `Bearer ${apiKey}`
                }
            });

            vscode.window.showInformationMessage('✓ Workflow deployed successfully');
        } catch (e) {
            vscode.window.showErrorMessage(`Deployment failed: ${e}`);
        }
    });

    // Auto-validate on save
    let saveDisposable = vscode.workspace.onDidSaveTextDocument(async (document) => {
        const config = vscode.workspace.getConfiguration('dify');
        if (config.get<boolean>('autoValidate', true)) {
            if (document.fileName.endsWith('.yml') || document.fileName.endsWith('.yaml')) {
                try {
                    yaml.load(document.getText());
                    vscode.window.setStatusBarMessage('$(check) Dify: Valid', 3000);
                } catch (e) {
                    vscode.window.setStatusBarMessage('$(error) Dify: Invalid YAML', 5000);
                }
            }
        }
    });

    context.subscriptions.push(
        previewCommand,
        validateCommand,
        visualizeCommand,
        exportPythonCommand,
        deployCommand,
        saveDisposable
    );
}

export function deactivate() {}
