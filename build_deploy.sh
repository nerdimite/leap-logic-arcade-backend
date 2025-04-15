#!/bin/bash

ACCOUNT_ID=800756380562
PROJECT_NAME=logic-arcade-backend

# Build the Docker image
# docker build -t $PROJECT_NAME .

# Create ECR repository if it doesn't exist
# aws ecr create-repository --repository-name $PROJECT_NAME --region us-east-1 --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag and push the Docker image to ECR
docker tag $PROJECT_NAME:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/$PROJECT_NAME:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/$PROJECT_NAME:latest
