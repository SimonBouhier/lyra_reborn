"""Fixture publique unique des smoke-tests P7 ; jamais un cas de campagne."""

MODEL_DIGESTS = {
    "mistral:latest": "6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf",
    "gemma3:latest": "a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a",
    "granite3.3:latest": "fd429f23b90980ed1bef53b990894e7b0199331f6ae90c5650240a7d5b70f1f7",
}

SYNTHETIC_SOURCE = (
    "Adaptive policies can change decoding parameters after observing a first "
    "draft, but the resulting decision still requires independent evidence "
    "and a held-out comparison before promotion."
)
