"""FileKind: what a changed file is (source, test, migration, config, ...), from its path alone."""
import re

RULES = (
    ("noise", r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|Gemfile\.lock|poetry\.lock|Pipfile\.lock|composer\.lock|"
              r"go\.sum|Cargo\.lock|uv\.lock|bun\.lockb)$|\.(min\.js|min\.css|map|snap)$|(^|/)(dist|build|vendor|node_modules)/"),
    ("test", r"(^|/)(tests?|spec|specs|__tests__|e2e|cypress|playwright)/|[._-](test|spec)\.[a-z]+$|_test\.(go|py|rb|exs?)$|^test_.*\.py$|/test_[^/]*\.py$"),
    ("migration", r"(^|/)(db/migrate|migrations?|alembic/versions|priv/repo/migrations|flyway|liquibase)/|\.sql$"),
    ("schema", r"(^|/)(db/schema\.rb|db/structure\.sql|schema\.prisma|schema\.graphql|.*\.graphql|openapi\.(ya?ml|json)|swagger\.(ya?ml|json))$|\.proto$"),
    ("dependency", r"(^|/)(package\.json|Gemfile|requirements[^/]*\.txt|pyproject\.toml|Pipfile|go\.mod|Cargo\.toml|composer\.json|mix\.exs|pom\.xml|build\.gradle(\.kts)?)$"),
    ("ci", r"(^|/)(\.github/workflows|\.gitlab-ci\.yml|\.circleci|Jenkinsfile|\.buildkite|azure-pipelines\.yml|bitbucket-pipelines\.yml)"),
    ("infra", r"(^|/)(Dockerfile[^/]*|docker-compose[^/]*\.ya?ml|k8s/|helm/|charts/|terraform/|.*\.tf|Procfile|fly\.toml|serverless\.ya?ml)"),
    ("config", r"(^|/)(config/|settings/|\.env[^/]*|[^/]*\.(ya?ml|toml|ini|cfg|conf)$)|(^|/)(routes\.rb|settings\.py|next\.config\.[jt]s|vite\.config\.[jt]s|tsconfig\.json|webpack\.config\.[jt]s)$"),
    ("docs", r"\.(md|mdx|rst|adoc|txt)$|(^|/)docs?/"),
    ("asset", r"\.(png|jpe?g|gif|svg|ico|webp|woff2?|ttf|eot|pdf|mp4|mp3)$"),
    ("style", r"\.(css|scss|sass|less|styl)$"),
)
COMPILED = tuple((kind, re.compile(rx, re.I)) for kind, rx in RULES)
ORDER = ("source", "test", "migration", "schema", "dependency", "config", "infra", "ci", "style", "docs", "asset", "noise")


class FileKind(object):
    @staticmethod
    def of(path):
        for kind, rx in COMPILED:
            if rx.search(path):
                return kind
        return "source"

    @staticmethod
    def area(path):
        """A short grouping key: the first two folders of the path (app/models, src/components, ...)."""
        return "/".join(path.split("/")[:-1][:2]) or "(root)"
