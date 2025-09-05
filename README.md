# A Reference Model for Secure AI in Splunk

We believe that AI can be a powerful tool for Splunk users, but we also know that deploying AI in a production environment brings a unique set of challenges. This project is our attempt to provide a reference model for how to do it safely, securely, and in a way that will satisfy your security, compliance, and audit teams.

## The Challenge: Bridging the Gap Between AI and the Enterprise

Many of us are excited about the potential of AI, but we also have to answer tough questions from our colleagues:

*   **Security:** "How can we be sure the AI won't run a dangerous command?"
*   **Compliance:** "How do we audit what the AI is doing? Can we prove it's not accessing sensitive data?"
*   **Reliability:** "How can we get consistent and predictable results from the AI?"

Simple AI integrations often work well in a lab, but they can be difficult to deploy in a real-world enterprise environment where these questions must be answered.

### The Problem with "AI Does Whatever It Wants"

When AI has direct access to Splunk APIs, it makes decisions in isolation - guessing at index names, creating inefficient searches, and potentially exposing sensitive data. Every interaction is different, making it impossible to ensure consistent, safe behavior.

We believe the solution is a controlled approach: instead of letting AI improvise, we provide version-controlled guidance that ensures AI follows your organization's best practices every time. This creates a reliable "choke point" where you can enforce data protection, search efficiency, and compliance requirements before any query runs.

## Our Approach: Configuration as Code

Instead of embedding security policies and AI logic deep within the application code, we've taken a different approach. We believe that everything important should be defined in simple, human-readable configuration files.

This means that your security policies, your data masking rules, and even the AI's behavior are all defined in version-controlled `YAML` files.

For example, here's how you can define a security policy in `guardrails.yaml`:

```yaml
# guardrails.yaml - A clear, auditable security policy
blocked_commands:
  - "|delete"
  - "|outputlookup"
  - "|sendemail"

sensitive_fields:
  - "password"
  - "ssn"
  - "credit_card"
```

When your auditor asks to see your security policies, you don't have to show them Python code. You can show them this file.

## What This Reference Model Offers

This approach provides a number of benefits:

*   **For Security Teams:** A clear, auditable, and version-controlled security policy that can be reviewed and approved without needing to be a programmer.
*   **For Compliance and Audit Teams:** A complete audit trail of all policy changes. `git log guardrails.yaml` shows you who changed what, when, and why.
*   **For Splunk Admins and Operations Teams:** A more predictable and reliable AI that can be configured to follow your organization's best practices.

## Deployment Options and Validation

We've designed this reference model to work in different environments and use cases:

*   **Web Portal Integration:** Complete audit-ready interface with session management and user tracking
*   **MCP Server (MCP-only):** Lightweight integration with existing AI tools like Claude Desktop
*   **Development Environment:** Testing setup with sample Splunk data for evaluation

To ensure reliability, we've built comprehensive validation into the reference model. Our automated testing covers security guardrails, deployment procedures, and cross-platform compatibility. We believe that trust in AI systems comes from transparent validation of their behavior.

## Is This For You?

This project is for you if you are a Splunk customer, administrator, or security professional who is:

*   Exploring how to use AI with Splunk in a secure and compliant way.
*   Looking for a reference model or a set of patterns that you can adapt to your own environment.
*   Interested in a "Configuration as Code" approach to managing AI security and governance.

This is not a "plug-and-play" solution, but rather a set of tools and patterns that we hope will be useful to the community.

## Prerequisites

Before you begin, ensure you have:

*   **Docker and Docker Compose:** Required for containerized deployment
*   **API Keys (for web interface option):** At least one of:
    *   `ANTHROPIC_API_KEY` - For Claude models (recommended)
    *   `OPENAI_API_KEY` - For OpenAI GPT models
    *   `GOOGLE_API_KEY` - For Google Gemini models
*   **Splunk Access:** Connection details for your Splunk instance

## Getting Started

While this isn't a plug-and-play solution, we've created a set of documents to help you get started. We hope you'll find them useful.

*   **[Pack Setup Guide](docs/pack-setup.md):** This is the best place to start. It will walk you through the installation and configuration process.
*   **[Architecture Overview](docs/architecture.md):** If you want to understand how all the pieces fit together, this document provides a high-level overview of the system's architecture.
*   **[Security Guardrails](docs/security-guardrails.md):** This document details the security features of the project and explains how to configure them.
*   **[Usage Examples](docs/examples.md):** See the system in action with a variety of real-world usage examples.
*   **[Prompt Workflows](docs/prompt-workflows.md):** Learn how we use prompts to guide the AI's behavior and ensure consistent results.

**For those ready to evaluate:** We've created interactive deployment scripts (`scripts/deploy.sh` or `scripts/deploy.bat`) that guide you through the setup process and help you choose the right deployment option for your environment.

## Our Philosophy and Invitation to Collaborate

We are sharing this project in the hope that it will be a useful starting point for others who are facing the same challenges we are. We are not claiming to have all the answers, and we are eager to learn from the community.

We welcome your feedback, your questions, and your contributions. Please feel free to open an issue, start a discussion, or submit a pull request.