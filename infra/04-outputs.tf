# outputs.tf

# ##############################
# VPC
# ##############################
output "vpc_id" {
  description = "ID of the VPC."
  value       = module.vpc.vpc_id
}

# ##############################
# EKS
# ##############################
output "kubeconfig_command" {
  description = "Command to update local kubeconfig."
  value       = "aws eks update-kubeconfig --region ${local.region} --name ${module.eks.cluster_name}"
}

# ##############################
# Karpenter
# ##############################
output "karpenter_cluster_name" {
  description = "EKS cluster name."
  value       = module.eks.cluster_name
}
output "karpenter_node_iam_role_name" {
  description = "Node IAM role name."
  value       = module.karpenter.node_iam_role_name
}

output "karpenter_queue_name" {
  description = "SQS interruption queue name."
  value       = module.karpenter.queue_name
}
