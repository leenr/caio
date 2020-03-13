import asyncio

import os
import sys
import time

from caio import AsyncioAIOContext


loop = asyncio.get_event_loop()


chunk_size = 32 * 1024
context_max_requests = 512


async def read_file(ctx: AsyncioAIOContext, file_id):
    offset = 0
    fname = f"data/{file_id}.bin"
    file_size = os.stat(fname).st_size

    futures = []

    with open(fname, "rb") as fp:
        fd = fp.fileno()

        while offset < file_size:
            futures.append(ctx.read(chunk_size, fd, offset))
            offset += chunk_size

        await asyncio.gather(*futures)

    return len(futures)


async def timer(future):
    await asyncio.sleep(0)
    delta = time.monotonic()
    return await future, time.monotonic() - delta


async def main():
    for generation in range(1, 129):
        context = AsyncioAIOContext(context_max_requests)

        futures = []

        for file_id in range(generation):
            futures.append(read_file(context, file_id))

        stat = []
        total = - time.monotonic()
        nops = 0

        for ops, delta in await asyncio.gather(*map(timer, futures)):
            stat.append(delta)
            nops += ops

        total += time.monotonic()

        stat = sorted(stat)

        ops_sec = nops / total

        dmin = stat[0]
        dmedian = stat[int(len(stat) / 2)]
        dmax = (stat[-1])

        sys.stdout.write(
            "\t".join(
                map(lambda x: str(x).replace(".", ","), (
                    generation, context_max_requests,
                    dmin, dmedian, dmax,
                    ops_sec, total, nops, chunk_size
                )))
        )
        sys.stdout.write("\n")
        sys.stdout.flush()

        await context.close()


if __name__ == '__main__':
    loop.run_until_complete(main())