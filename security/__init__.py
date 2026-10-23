"""Database-at-rest encryption for Viper.

Pure-Python envelope encryption (see `security.envelope`) plus the working-copy
lifecycle that uses it (see `security.encrypted_database`). No compiled/native
dependencies — see PROJECT_PLAN.md and repo memory for why SQLCipher was
evaluated and not chosen.
"""
