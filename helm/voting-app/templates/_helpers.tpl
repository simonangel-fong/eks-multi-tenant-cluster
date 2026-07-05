{{/*
Chart name.
*/}}
{{- define "voting-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Fully qualified app name — release name + chart name, capped at 63 chars.
*/}}
{{- define "voting-app.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Chart label (chart-version).
*/}}
{{- define "voting-app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels applied to every resource.
*/}}
{{- define "voting-app.labels" -}}
helm.sh/chart: {{ include "voting-app.chart" . }}
{{ include "voting-app.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: voting-app
{{- end -}}

{{/*
Selector labels — stable across upgrades; do not include version.
*/}}
{{- define "voting-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "voting-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Component-scoped names + selectors.
Usage: {{ include "voting-app.api.fullname" . }}
*/}}
{{- define "voting-app.api.fullname" -}}
{{- printf "%s-api" (include "voting-app.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "voting-app.api.selectorLabels" -}}
{{ include "voting-app.selectorLabels" . }}
app.kubernetes.io/component: api
{{- end -}}

{{- define "voting-app.postgres.fullname" -}}
{{- printf "%s-postgres" (include "voting-app.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "voting-app.postgres.selectorLabels" -}}
{{ include "voting-app.selectorLabels" . }}
app.kubernetes.io/component: postgres
{{- end -}}

{{/*
Postgres secret name — respects existingSecret so out-of-band prod secrets work.
*/}}
{{- define "voting-app.postgres.secretName" -}}
{{- if .Values.postgres.auth.existingSecret -}}
{{- .Values.postgres.auth.existingSecret -}}
{{- else -}}
{{- include "voting-app.postgres.fullname" . -}}
{{- end -}}
{{- end -}}

{{/*
Gateway parentRef name — defaults to the in-chart Gateway when createGateway=true.
*/}}
{{- define "voting-app.gateway.parentRefName" -}}
{{- if .Values.gateway.parentRef.name -}}
{{- .Values.gateway.parentRef.name -}}
{{- else -}}
{{- include "voting-app.api.fullname" . -}}
{{- end -}}
{{- end -}}
