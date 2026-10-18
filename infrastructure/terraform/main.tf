# Terraform Main Configuration

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
  
  backend "s3" {
    bucket         = "scalable-pipelines-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "scalable-data-pipelines"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
  }
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "scalable-pipelines"
}

# Random suffix for unique names
resource "random_id" "suffix" {
  byte_length = 4
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC Module
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  name = "${var.cluster_name}-${var.environment}"
  cidr = var.vpc_cidr
  
  azs             = data.aws_availability_zones.available.names
  private_subnets = [for k, v in data.aws_availability_zones.available.names : cidrsubnet(var.vpc_cidr, 4, k)]
  public_subnets  = [for k, v in data.aws_availability_zones.available.names : cidrsubnet(var.vpc_cidr, 8, k)]
  
  enable_nat_gateway     = true
  single_nat_gateway     = var.environment == "dev"
  enable_dns_hostnames   = true
  enable_dns_support     = true
  
  tags = {
    Environment = var.environment
  }
}

# EKS Cluster Module
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  
  cluster_name    = "${var.cluster_name}-${var.environment}"
  cluster_version = "1.28"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  eks_managed_node_group_defaults = {
    ami_type       = "AL2_x86_64"
    instance_types = ["m5.large"]
  }
  
  eks_managed_node_groups = {
    general = {
      name           = "general"
      instance_types = ["m5.large"]
      capacity_type  = "ON_DEMAND"
      
      min_size     = var.environment == "prod" ? 3 : 1
      max_size     = var.environment == "prod" ? 10 : 5
      desired_size = var.environment == "prod" ? 3 : 2
      
      labels = {
        Environment = var.environment
        NodeGroup   = "general"
      }
    }
    
    compute = {
      name           = "compute"
      instance_types = ["r5.xlarge"]
      capacity_type  = "SPOT"
      
      min_size     = 0
      max_size     = var.environment == "prod" ? 20 : 5
      desired_size = 0
      
      labels = {
        Environment = var.environment
        NodeGroup   = "compute"
        WorkloadType = "batch"
      }
      
      taints = [{
        key    = "workload"
        value  = "batch"
        effect = "NO_SCHEDULE"
      }]
    }
  }
  
  # Enable IRSA for service accounts
  enable_irsa = true
  
  tags = {
    Environment = var.environment
  }
}

# S3 Buckets for Data Lake
resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.cluster_name}-data-lake-${var.environment}-${random_id.suffix.hex}"
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    enabled = true
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
  
  tags = {
    Environment = var.environment
    Purpose     = "data-lake"
  }
}

resource "aws_s3_bucket" "checkpoints" {
  bucket = "${var.cluster_name}-checkpoints-${var.environment}-${random_id.suffix.hex}"
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
  
  lifecycle_rule {
    enabled = true
    expiration {
      days = 7
    }
  }
  
  tags = {
    Environment = var.environment
    Purpose     = "checkpoints"
  }
}

# RDS for Metadata
resource "aws_db_instance" "metadata" {
  identifier = "${var.cluster_name}-metadata-${var.environment}"
  
  engine               = "postgres"
  engine_version       = "15.4"
  instance_class       = var.environment == "prod" ? "db.r6g.large" : "db.t3.micro"
  allocated_storage    = 20
  max_allocated_storage = 100
  storage_encrypted    = true
  
  db_name  = "metadata"
  username = "admin"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = var.environment == "prod" ? 7 : 1
  skip_final_snapshot     = var.environment != "prod"
  deletion_protection     = var.environment == "prod"
  
  tags = {
    Environment = var.environment
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.cluster_name}-db-subnet-${var.environment}"
  subnet_ids = module.vpc.private_subnets
  
  tags = {
    Environment = var.environment
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.cluster_name}-rds-sg-${var.environment}"
  description = "Security group for RDS"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }
  
  tags = {
    Environment = var.environment
  }
}

# ECR Repositories
resource "aws_ecr_repository" "batch" {
  name = "${var.cluster_name}/batch-pipeline"
  
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_repository" "streaming" {
  name = "${var.cluster_name}/streaming-pipeline"
  
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  encryption_configuration {
    encryption_type = "AES256"
  }
}

# IAM Roles for Service Accounts (IRSA)
resource "aws_iam_role" "spark_sa" {
  name = "${var.cluster_name}-spark-sa-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(module.eks.cluster_oidc_issuer_url, "https://", "")}"
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${replace(module.eks.cluster_oidc_issuer_url, "https://", "")}:sub" = "system:serviceaccount:data-pipelines:spark"
        }
      }
    }]
  })
}

resource "aws_iam_policy" "spark_s3_access" {
  name = "${var.cluster_name}-spark-s3-${var.environment}"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*",
          aws_s3_bucket.checkpoints.arn,
          "${aws_s3_bucket.checkpoints.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "spark_s3" {
  role       = aws_iam_role.spark_sa.name
  policy_arn = aws_iam_policy.spark_s3_access.arn
}

data "aws_caller_identity" "current" {}

# Outputs
output "vpc_id" {
  value = module.vpc.vpc_id
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "data_lake_bucket" {
  value = aws_s3_bucket.data_lake.bucket
}

output "checkpoints_bucket" {
  value = aws_s3_bucket.checkpoints.bucket
}

output "ecr_batch_repo" {
  value = aws_ecr_repository.batch.repository_url
}

output "ecr_streaming_repo" {
  value = aws_ecr_repository.streaming.repository_url
}