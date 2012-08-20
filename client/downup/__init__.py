"""
DownUp module

This module handles every asynchronous upload and download. This is where the
magic is performed, through a dedicated scheduler and an abstraction layer.

Tasks (upload and download tasks) are managed through their UUIDs, and managers
provide an easy way to create, remove, and handle as upload and download tasks
as the scheduler.
"""