# Org-standard TFLint configuration for Nexus Terraform repositories.
# Source of truth: nexus-terraform/.tflint.hcl — keep in sync.
# Copy to the repository root as .tflint.hcl.

config {
  module = true
}

rule "terraform_unused_declarations" {
  enabled = true
}

rule "terraform_comment_syntax" {
  enabled = true
}

rule "terraform_documented_outputs" {
  enabled = true
}

rule "terraform_typed_variables" {
  enabled = true
}

rule "terraform_naming_convention" {
  enabled = true
}

rule "terraform_required_version" {
  enabled = true
}

rule "terraform_required_providers" {
  enabled = true
}

rule "terraform_standard_module_structure" {
  enabled = false
}

rule "terraform_module_pinned_source" {
  enabled = false
}

plugin "aws" {
  enabled = true
  version = "0.22.1"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}
