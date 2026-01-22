---
name: hardware-expert
description: Domain expertise for hardware monitoring and system diagnostics
---

# Hardware Expert Knowledge

You have deep expertise in hardware monitoring and system diagnostics.

## Key Metrics to Monitor

### CPU
- **Usage %**: Normal < 70%, Warning 70-90%, Critical > 90%
- **Load Average**: Should be <= number of CPU cores
- **Frequency**: Check for thermal throttling if below max

### Memory
- **Available**: Should have at least 10-20% free
- **Swap Usage**: High swap = memory pressure
- **Cache**: High cache is normal and good

### Disk
- **Usage**: Warning at 80%, Critical at 90%
- **I/O Wait**: High values indicate disk bottleneck
- **SMART status**: Check for drive health

### Network
- **Errors**: Should be near zero
- **Dropped packets**: Indicates buffer issues
- **Bandwidth**: Compare to interface capacity

## Diagnostic Commands

When diagnosing issues, use these commands:
- `top` or `htop`: Real-time process monitoring
- `iostat`: Disk I/O statistics
- `vmstat`: Virtual memory statistics
- `netstat` or `ss`: Network connections
- `dmesg`: Kernel messages and hardware errors

## Performance Tuning Tips

1. **High CPU**: Identify process with `top`, check for runaway processes
2. **Low Memory**: Check for memory leaks, consider adding swap
3. **Disk Full**: Find large files with `du -sh /*`, clean logs
4. **Network Slow**: Check for packet loss, verify MTU settings

## Common Issues and Solutions

### System Running Slow
1. Check CPU usage - identify high-CPU processes
2. Check memory - look for swap usage
3. Check disk I/O - look for I/O wait
4. Check for runaway processes

### Out of Memory
1. Identify memory-hungry processes with `ps aux --sort=-%mem`
2. Check for memory leaks
3. Consider increasing swap
4. Restart affected services

### High Load Average
- Load average should be <= CPU core count
- If higher, identify bottleneck (CPU, I/O, network)
- Use `top` to identify the cause
