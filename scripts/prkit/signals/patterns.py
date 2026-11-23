"""The regular expressions behind the caveat signals (shared with the description checks: SECRET)."""
import re

ENV_VAR = re.compile(r"ENV\[\s*['\"]([A-Z0-9_]+)|ENV\.fetch\(\s*['\"]([A-Z0-9_]+)|process\.env\.([A-Z0-9_]+)|"
                     r"process\.env\[\s*['\"]([A-Z0-9_]+)|os\.environ(?:\.get)?[\[(]\s*['\"]([A-Z0-9_]+)|"
                     r"os\.getenv\(\s*['\"]([A-Z0-9_]+)|System\.getenv\(\s*\"([A-Z0-9_]+)|import\.meta\.env\.([A-Z0-9_]+)|"
                     r"System\.get_env\(\s*\"([A-Z0-9_]+)|^\+?\s*([A-Z][A-Z0-9_]{2,})\s*=", re.M)
FLAG = re.compile(r"Flipper|LaunchDarkly|ldclient|Unleash|unleash|feature_?flag|featureFlag|isFeatureEnabled|"
                  r"FeatureFlag|Split\.io|growthbook|flagsmith|posthog\.isFeatureEnabled", re.I)
ROUTE = re.compile(r"^\s*(get|post|put|patch|delete|resources?|namespace|scope|match)\s+['\":(]|"
                   r"@(app|router|bp|blueprint)\.(get|post|put|patch|delete|route)\(|"
                   r"\b(router|app|server)\.(get|post|put|patch|delete|use)\(\s*['\"`]/|"
                   r"@(Get|Post|Put|Patch|Delete|Request)Mapping|path\(\s*['\"]|"
                   r"\bfield\s+:\w+|\bmutation\s+\w|type\s+(Query|Mutation)\b|export\s+(async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE)\b")
PUBLIC_DEF = re.compile(r"^\s*(def\s+(?!_)\w+|public\s+[\w<>\[\]]+\s+\w+\s*\(|export\s+(default\s+)?(async\s+)?(function|class|const)\s+\w+|"
                        r"func\s+[A-Z]\w*|class\s+\w+|module\s+\w+)")
TODO = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
DEBUG = re.compile(r"\bconsole\.(log|debug)\(|\bbinding\.pry\b|\bbyebug\b|\bdebugger\b|\bpdb\.set_trace\(|\bbreakpoint\(\)|"
                   r"\bdd\(|\bvar_dump\(|\bIO\.inspect\b|\bputs\s+[\"'#]|\bpp\s+\w")
PY_PRINT = re.compile(r"^\s*print\(")
SECRET = re.compile(r"AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[abpr]-[0-9A-Za-z-]{10,}|gh[pousr]_[0-9A-Za-z]{30,}|"
                    r"sk-[A-Za-z0-9]{20,}|(password|passwd|secret|api_?key|token)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]", re.I)
