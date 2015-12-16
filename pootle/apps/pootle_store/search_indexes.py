import datetime

from haystack import indexes

from pootle_store.models import Unit, Store


class UnitIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(
        document=True, use_template=True)
    id = indexes.IntegerField(
        model_attr='id')
    index = indexes.IntegerField(
        model_attr='index')
    unitid = indexes.CharField(
        model_attr='unitid')
    source = indexes.CharField(
        model_attr='source_f')
    target = indexes.CharField(
        model_attr='target_f')
    pootle_path = indexes.CharField(
        model_attr='store__pootle_path')
    priority = indexes.IntegerField(
        model_attr='priority')
    revision = indexes.IntegerField(
        model_attr='revision')
    state = indexes.IntegerField(
        model_attr='state')
    store = indexes.IntegerField(
        model_attr='store__pk')
    project = indexes.IntegerField(
        model_attr='store__translation_project__project__pk')
    language = indexes.IntegerField(
        model_attr='store__translation_project__language__pk')
    source_language = indexes.CharField(
        model_attr='store__translation_project__project__source_language__code')
    translation_project = indexes.IntegerField(
        model_attr='store__translation_project__pk')
    mtime = indexes.DateTimeField(
        model_attr='mtime')
    creation_time = indexes.DateTimeField(
        model_attr='creation_time', null=True)

    submitted_by = indexes.CharField(
        model_attr='submitted_by__username', null=True)
    submitted_on = indexes.DateTimeField(
        model_attr='submitted_on', null=True)

    commented_by = indexes.CharField(
        model_attr='commented_by__username', null=True)
    commented_on = indexes.DateTimeField(
        model_attr='commented_on', null=True)

    reviewed_by = indexes.CharField(
        model_attr='reviewed_by__username', null=True)
    reviewed_on = indexes.DateTimeField(
        model_attr='reviewed_on', null=True)

    developer_comment = indexes.CharField(
        model_attr='developer_comment', null=True)
    translator_comment = indexes.CharField(
        model_attr='translator_comment', null=True)

    nplurals = indexes.IntegerField(
        model_attr='store__translation_project__language__nplurals')

    # exact search
    language_code = indexes.EdgeNgramField(
        model_attr='store__translation_project__language__code')
    project_code = indexes.EdgeNgramField(
        model_attr='store__translation_project__project__code')
    source_language_code = indexes.EdgeNgramField(
        model_attr='store__translation_project__project__source_language__code')
    project_checkstyle = indexes.EdgeNgramField(
        model_attr='store__translation_project__project__checkstyle') 

    checks = indexes.MultiValueField()

    suggestions = indexes.MultiValueField()
    suggested_by = indexes.CharField()
    suggestion_state = indexes.CharField()

    def get_model(self):
        return Unit

    def prepare_checks(self, obj):
        return [
            check
            for check
            in obj.qualitycheck_set.values_list("pk", flat=True)]

    def _get_suggestions(self, obj):
        return obj.suggestion_set.order_by(
            "-review_time", "-creation_time")

    def prepare_suggestions(self, obj):        
        return [
            suggestion
            for suggestion
            in self._get_suggestions(obj).values_list("pk", flat=True)]

    def prepare_suggested_by(self, obj):
        suggestions = self._get_suggestions(obj)
        if suggestions.exists():
            return suggestions[0].user.username

    def prepare_suggestion_state(self, obj):
        suggestions = self._get_suggestions(obj)
        if suggestions.exists():
            return suggestions[0].user.username
