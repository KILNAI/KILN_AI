import os
from pathlib import Path

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

import kiln_ai.datamodel as datamodel
from kiln_ai.adapters.adapter_registry import adapter_for_task
from kiln_ai.adapters.langchain_adapters import LangchainAdapter
from kiln_ai.adapters.ml_model_list import built_in_models
from kiln_ai.adapters.ollama_tools import ollama_online
from kiln_ai.adapters.prompt_builders import (
    BasePromptBuilder,
    SimpleChainOfThoughtPromptBuilder,
)


def get_all_models_and_providers():
    model_provider_pairs = []
    for model in built_in_models:
        for provider in model.providers:
            model_provider_pairs.append((model.name, provider.name))
    return model_provider_pairs


@pytest.mark.paid
async def test_groq(tmp_path):
    if os.getenv("GROQ_API_KEY") is None:
        pytest.skip("GROQ_API_KEY not set")
    await run_simple_test(tmp_path, "llama_3_1_8b", "groq")


@pytest.mark.parametrize(
    "model_name",
    [
        "llama_3_1_8b",
        "llama_3_1_70b",
        "gemini_1_5_pro",
        "gemini_1_5_flash",
        "gemini_1_5_flash_8b",
        "nemotron_70b",
        "llama_3_2_3b",
        "llama_3_2_11b",
        "llama_3_2_90b",
        "claude_3_5_haiku",
        "claude_3_5_sonnet",
        "phi_3_5",
    ],
)
@pytest.mark.paid
async def test_openrouter(tmp_path, model_name):
    await run_simple_test(tmp_path, model_name, "openrouter")


@pytest.mark.ollama
async def test_ollama_phi(tmp_path):
    # Check if Ollama API is running
    if not await ollama_online():
        pytest.skip("Ollama API not running. Expect it running on localhost:11434")

    await run_simple_test(tmp_path, "phi_3_5", "ollama")


@pytest.mark.ollama
async def test_ollama_gemma(tmp_path):
    # Check if Ollama API is running
    if not await ollama_online():
        pytest.skip("Ollama API not running. Expect it running on localhost:11434")

    await run_simple_test(tmp_path, "gemma_2_2b", "ollama")


@pytest.mark.ollama
async def test_autoselect_provider(tmp_path):
    # Check if Ollama API is running
    if not await ollama_online():
        pytest.skip("Ollama API not running. Expect it running on localhost:11434")

    await run_simple_test(tmp_path, "phi_3_5")


@pytest.mark.ollama
async def test_ollama_llama(tmp_path):
    # Check if Ollama API is running
    if not await ollama_online():
        pytest.skip("Ollama API not running. Expect it running on localhost:11434")

    await run_simple_test(tmp_path, "llama_3_1_8b", "ollama")


@pytest.mark.paid
async def test_openai(tmp_path):
    if os.getenv("OPENAI_API_KEY") is None:
        pytest.skip("OPENAI_API_KEY not set")
    await run_simple_test(tmp_path, "gpt_4o_mini", "openai")


@pytest.mark.paid
async def test_amazon_bedrock(tmp_path):
    if (
        os.getenv("AWS_SECRET_ACCESS_KEY") is None
        or os.getenv("AWS_ACCESS_KEY_ID") is None
    ):
        pytest.skip("AWS keys not set")
    await run_simple_test(tmp_path, "llama_3_1_8b", "amazon_bedrock")


async def test_mock(tmp_path):
    task = build_test_task(tmp_path)
    mockChatModel = FakeListChatModel(responses=["mock response"])
    adapter = LangchainAdapter(task, custom_model=mockChatModel)
    run = await adapter.invoke("You are a mock, send me the response!")
    assert "mock response" in run.output.output


async def test_mock_returning_run(tmp_path):
    task = build_test_task(tmp_path)
    mockChatModel = FakeListChatModel(responses=["mock response"])
    adapter = LangchainAdapter(task, custom_model=mockChatModel)
    run = await adapter.invoke("You are a mock, send me the response!")
    assert run.output.output == "mock response"
    assert run is not None
    assert run.id is not None
    assert run.input == "You are a mock, send me the response!"
    assert run.output.output == "mock response"
    assert "created_by" in run.input_source.properties
    assert run.output.source.properties == {
        "adapter_name": "kiln_langchain_adapter",
        "model_name": "custom.langchain:unknown_model",
        "model_provider": "custom.langchain:FakeListChatModel",
        "prompt_builder_name": "simple_prompt_builder",
    }


@pytest.mark.paid
@pytest.mark.ollama
@pytest.mark.parametrize("model_name,provider_name", get_all_models_and_providers())
async def test_all_models_providers_plaintext(tmp_path, model_name, provider_name):
    task = build_test_task(tmp_path)
    await run_simple_task(task, model_name, provider_name)


@pytest.mark.paid
@pytest.mark.ollama
@pytest.mark.parametrize("model_name,provider_name", get_all_models_and_providers())
async def test_cot_prompt_builder(tmp_path, model_name, provider_name):
    task = build_test_task(tmp_path)
    pb = SimpleChainOfThoughtPromptBuilder(task)
    await run_simple_task(task, model_name, provider_name, pb)


def build_test_task(tmp_path: Path):
    project = datamodel.Project(name="test", path=tmp_path / "test.kiln")
    project.save_to_file()
    assert project.name == "test"

    r1 = datamodel.TaskRequirement(
        name="BEDMAS",
        instruction="You follow order of mathematical operation (BEDMAS)",
    )
    r2 = datamodel.TaskRequirement(
        name="only basic math",
        instruction="If the problem has anything other than addition, subtraction, multiplication, division, and brackets, you will not answer it. Reply instead with 'I'm just a basic calculator, I don't know how to do that'.",
    )
    r3 = datamodel.TaskRequirement(
        name="Answer format",
        instruction="The answer can contain any content about your reasoning, but at the end it should include the final answer in numerals in square brackets. For example if the answer is one hundred, the end of your response should be [100].",
    )
    task = datamodel.Task(
        parent=project,
        name="test task",
        instruction="You are an assistant which performs math tasks provided in plain text.",
        requirements=[r1, r2, r3],
    )
    task.save_to_file()
    assert task.name == "test task"
    assert len(task.requirements) == 3
    return task


async def run_simple_test(
    tmp_path: Path,
    model_name: str,
    provider: str | None = None,
    prompt_builder: BasePromptBuilder | None = None,
):
    task = build_test_task(tmp_path)
    return await run_simple_task(task, model_name, provider, prompt_builder)


async def run_simple_task(
    task: datamodel.Task,
    model_name: str,
    provider: str,
    prompt_builder: BasePromptBuilder | None = None,
) -> datamodel.TaskRun:
    adapter = adapter_for_task(
        task, model_name=model_name, provider=provider, prompt_builder=prompt_builder
    )

    run = await adapter.invoke(
        "You should answer the following question: four plus six times 10"
    )
    assert "64" in run.output.output
    assert run.id is not None
    assert (
        run.input == "You should answer the following question: four plus six times 10"
    )
    assert "64" in run.output.output
    source_props = run.output.source.properties
    assert source_props["adapter_name"] == "kiln_langchain_adapter"
    assert source_props["model_name"] == model_name
    assert source_props["model_provider"] == provider
    expected_prompt_builder_name = (
        prompt_builder.__class__.prompt_builder_name()
        if prompt_builder
        else "simple_prompt_builder"
    )
    assert source_props["prompt_builder_name"] == expected_prompt_builder_name
    return run