from app.services.command_parser import parse_voice_command


def test_forward_to_ramp_parses_target():
    cmd = parse_voice_command("forward item gphoto_1 to ramp")
    assert cmd.command == "forward_to_ramp"
    assert cmd.target == "receipts@ramp.com"
