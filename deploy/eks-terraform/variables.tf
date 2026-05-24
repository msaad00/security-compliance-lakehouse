variable "region" {
  description = "AWS region for the EKS cluster + evidence bucket."
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "EKS cluster name."
  type        = string
  default     = "trustops"
}

variable "cluster_version" {
  description = "EKS Kubernetes version."
  type        = string
  default     = "1.30"
}

variable "namespace" {
  description = "Kubernetes namespace the TrustOps chart installs into."
  type        = string
  default     = "trustops"
}

variable "evidence_bucket_name" {
  description = "S3 bucket TrustOps reads evidence from. Customer-owned."
  type        = string
}

variable "evidence_bucket_arn_prefix" {
  description = "Optional ARN prefix (e.g. arn:aws:s3:::other-bucket) the IRSA role gets read-only access to."
  type        = string
  default     = ""
}

variable "ingress_host" {
  description = "Ingress hostname. Empty = no ingress."
  type        = string
  default     = ""
}

variable "image_repository" {
  description = "OCI image repo for the TrustOps workbench."
  type        = string
  default     = "ghcr.io/msaad00/trustops"
}

variable "image_tag" {
  description = "OCI image tag. Empty = chart appVersion default."
  type        = string
  default     = ""
}

variable "node_instance_types" {
  description = "EC2 instance types for the managed node group."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_min_size" {
  description = "Minimum node group size."
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Maximum node group size."
  type        = number
  default     = 3
}

variable "node_desired_size" {
  description = "Desired node group size."
  type        = number
  default     = 2
}

variable "tags" {
  description = "Extra AWS tags applied to every taggable resource."
  type        = map(string)
  default = {
    "trustops:component" = "workbench"
  }
}
