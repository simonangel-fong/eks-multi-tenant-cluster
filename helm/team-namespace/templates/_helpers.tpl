{{/*
Standard namespace name: <team>-<environment>
*/}}
{{- define "team-namespace.name" -}}
{{- printf "%s-%s" .Values.team .Values.environment -}}
{{- end -}}

{{/*
Common labels applied to every resource this chart creates.
*/}}
{{- define "team-namespace.labels" -}}
team: {{ .Values.team }}
environment: {{ .Values.environment }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: platform-tenancy
{{- end -}}
