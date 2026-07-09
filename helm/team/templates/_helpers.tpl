{{/*
Common labels for team-scoped resources.
*/}}
{{- define "team.labels" -}}
team: {{ .Values.team }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: platform-tenancy
{{- end -}}
