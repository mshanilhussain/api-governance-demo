#!/bin/bash

API_NAME="$1"

if [ -z "$API_NAME" ]; then
  echo "Usage: ./scripts/create-api.sh <api-name>"
  exit 1
fi

TEMPLATE="templates/api-template.yaml"
TARGET_DIR="specs/$API_NAME"
TARGET_FILE="$TARGET_DIR/$API_NAME.yaml"

if [ ! -f "$TEMPLATE" ]; then
  echo "Template not found: $TEMPLATE"
  exit 1
fi

if [ -d "$TARGET_DIR" ]; then
  echo "API already exists: $TARGET_DIR"
  exit 1
fi

mkdir -p "$TARGET_DIR"
cp "$TEMPLATE" "$TARGET_FILE"

echo "API created successfully:"
echo "$TARGET_FILE"