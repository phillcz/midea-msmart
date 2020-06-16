#!/usr/bin/env python3
import sys
import logging
import click
import json
from msmart.device import device as midea_device
from msmart.discover import discover as midea_discover


def connect(ip, id, retries=3):
    if not ip or not id:
        logging.error("IP address and ID required")
        sys.exit(1)

    logging.debug("Connect ip: %s id: %d", ip, id)

    for attempt in range(retries):
        try:
            client = midea_device(ip, id)
            device = client.setup()
            if not device:
                logging.error("Connect failed")
                continue

            device.refresh()
            return device

        except ValueError as error:
            if (attempt == retries - 1):
                raise error
            print(error)

    return device


def dump(device):
    j = {
        "online": device.online,
        "power_state": device.power_state,
        "operational_mode": device.operational_mode,
        "indoor_temperature": device.indoor_temperature,
        "outdoor_temperature": device.outdoor_temperature,
        "target_temperature": device.target_temperature,
        "fan_speed": device.fan_speed,
        "swing_mode": device.swing_mode,
        "eco_mode": device.eco_mode,
        "turbo_mode": device.turbo_mode,
    }
    print(json.dumps(j, indent=2, default=str))


def apply(device):
    device.apply


@click.group()
@click.option('-d', '--debug', help='Enable debug', is_flag=True)
@click.option('--ip', help='AC IP address')
@click.option('--id', help='AC ID', type=int)
@click.pass_context
def main(ctx, debug, ip, id):
    ctx.ensure_object(dict)
    ctx.obj['IP'] = ip
    ctx.obj['ID'] = id
    logging.basicConfig(format='%(levelname)s:%(message)s',
                        level=logging.DEBUG if debug else logging.INFO)

    pass


@main.command()
def discover():
    midea_discover(1)
    return


@main.command()
@click.pass_context
def info(ctx):
    device = connect(ctx.obj['IP'], ctx.obj['ID'])
    dump(device)
    return


@main.command()
@click.option('-m', '--mode',  default='current', help="(optional)", type=click.Choice(['current', 'auto', 'cool', 'dry', 'heat', 'fan'], case_sensitive=True))
@click.option('-t', '--temp',  default=-1, help="in Celsius (optional)", type=int)
@click.option('-s', '--speed', default=-1, help="[1..100]%, 0 - auto (optional)", type=click.IntRange(-1, 100))
@click.pass_context
def on(ctx, mode, temp, speed):
    device = connect(ctx.obj['IP'], ctx.obj['ID'])
    device.power_state = True
    device.prompt_tone = False

    if mode == 'auto':
        device.operational_mode = device.operational_mode_enum.auto
    elif mode == 'cool':
        device.operational_mode = device.operational_mode_enum.cool
    elif mode == 'dry':
        device.operational_mode = device.operational_mode_enum.dry
    elif mode == 'heat':
        device.operational_mode = device.operational_mode_enum.heat
    elif mode == 'fan':
        device.operational_mode = device.operational_mode_enum.fan_only

    if temp > -1:
        device.target_temperature = temp

    if speed == 0:
        device.fan_speed = 102  # Auto
    elif speed > 0 and speed <= 100:
        device.fan_speed = speed

    logging.debug("Apply")
    device.apply()


@main.command()
@click.pass_context
def off(ctx):
    device = connect(ctx.obj['IP'], ctx.obj['ID'])
    device.power_state = False
    device.prompt_tone = False

    logging.debug("Apply")
    device.apply()


if __name__ == '__main__':
    main()
