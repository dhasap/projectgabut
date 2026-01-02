#!/bin/bash
echo "🚀 Starting Deployment Process..."
echo "📦 Running Database Migration (Supabase -> Turso)..."
python3 migrate_supabase_to_turso.py
echo "✅ Migration Step Completed. Starting Bot..."
python3 bot.py