def generate_tfvars(custom_values: dict) -> str:
    lines = []
    for key, value in custom_values.items():
        if isinstance(value, str):
            lines.append(f'{key} = "{value}"')
        else:
            lines.append(f'{key} = {value}')
    return "\n".join(lines)
