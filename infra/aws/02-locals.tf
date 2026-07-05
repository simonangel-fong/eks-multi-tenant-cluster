locals {
  # ##############################
  # metadata
  # ##############################
  common_name = "${var.project}-${var.env}"
  default_tags = {
    Project     = var.project
    Environment = var.env
    ManagedBy   = "terraform"
  }


  # ##############################
  # VPC
  # ##############################
  subnet_azs = ["ca-central-1a", "ca-central-1b"]
  vpc_cidr   = "10.0.0.0/16"

  # ##############################
  # EKS
  # ##############################
  eks_name              = local.common_name
  eks_version           = "1.36"
  eks_node_type         = "t3.large"
  eks_node_desired_size = 3

}




