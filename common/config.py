from dotenv import load_dotenv
import os
# from phoenix.otel import register
from arize.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor
# Use BatchSpanProcessor for better performance in production
# from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

load_dotenv()

class Settings:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.arize_api_key = os.getenv("ARIZE_API_KEY")
        self.arize_space_id = os.getenv("ARIZE_SPACE_ID")
        self.arize_project_name = os.getenv("ARIZE_PROJECT_NAME", "lumen-adaptive-commerce")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self._validate()

    def _validate(self):
        missing = []
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not self.tavily_api_key:
            missing.append("TAVILY_API_KEY")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Please update your .env file."
            )

settings = Settings()


# Optional tracing (best-effort).
def initialize_arize_tracing(settings: Settings) -> None:
    """Initialize Arize instrumentation for LangChain/LangGraph tracing."""
    # Debug: Check if credentials are loaded
    has_api_key = bool(settings.arize_api_key)
    has_space_id = bool(settings.arize_space_id)
    print(f"[Arize] API Key configured: {has_api_key}")
    print(f"[Arize] Space ID configured: {has_space_id}")
    
    if not settings.arize_api_key or not settings.arize_space_id:
        print("[Arize] Missing credentials - tracing disabled")
        return

    try:
        from opentelemetry import trace
        # from opentelemetry.sdk.trace.export import BatchSpanProcessor
        
        print("[Arize] Initializing Arize tracing...")
        # Configure to use Arize's OTLP endpoint instead of localhost
        # This prevents "Transient error StatusCode.UNAVAILABLE" errors
        # os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "https://api.arize.com")

        # register() reads ARIZE_SPACE_ID and ARIZE_API_KEY from environment variables
        # tracer_provider = register(set_global_tracer_provider=False)
        tracer_provider = register(
            space_id=settings.arize_space_id,
            api_key=settings.arize_api_key,
            project_name=settings.arize_project_name,
            set_global_tracer_provider=False,
        )
        print(f"[Arize] Tracer provider created: {tracer_provider}")
        
        # batch_processor = BatchSpanProcessor(OTLPSpanExporter())
        # tracer_provider.add_span_processor(batch_processor)
        # print("[Arize] BatchSpanProcessor configured")
        
        # Set as global tracer provider
        trace.set_tracer_provider(tracer_provider)
        print("[Arize] Global tracer provider set")
        
        # Initialize instrumentation
        LangChainInstrumentor(tracer_provider=tracer_provider).instrument()
        print("[Arize] LangChain instrumentation complete")
    except Exception as e:
        print(f"[Arize] ERROR: Tracing initialization failed: {e}")
        import traceback
        traceback.print_exc()