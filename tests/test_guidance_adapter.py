import sys
import types


def install_fake_guidance():
    module = types.ModuleType("guidance")

    def gen(*, name, stream=False, **kwargs):  # pragma: no cover - simple fake
        return {"name": name, "stream": stream, "kwargs": kwargs}

    module.gen = gen
    sys.modules["guidance"] = module


def remove_fake_guidance():
    sys.modules.pop("guidance", None)


def run():
    install_fake_guidance()
    try:
        from proml.adapters.guidance_adapter import GuidanceGenerationAdapter

        adapter = GuidanceGenerationAdapter(variable_name="answer")
        adapter.apply_regex(r"^yes|no$")
        adapter.apply_json_schema({"type": "string"})
        adapter.apply_grammar({"start": "A"})

        kwargs = adapter.gen_kwargs()
        assert kwargs["regex"] == r"^yes|no$"
        assert kwargs["schema"] == {"type": "string"}
        assert kwargs["grammar"] == {"start": "A"}

        gen_call = adapter.gen_call(stream=True)
        assert gen_call["name"] == "answer"
        assert gen_call["stream"] is True
        assert gen_call["kwargs"]["regex"] == r"^yes|no$"
    finally:
        remove_fake_guidance()


if __name__ == "__main__":
    run()
    print("ok")
