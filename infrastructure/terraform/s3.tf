resource "aws_s3_bucket" "documents" {
  bucket = "${local.name_prefix}-documents-${data.aws_caller_identity.current.account_id}"

  tags = { Name = "${local.name_prefix}-documents" }
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id

  versioning_configuration {
    status = "Enabled"
  }
}

output "s3_bucket_documents" {
  value = aws_s3_bucket.documents.id
}
