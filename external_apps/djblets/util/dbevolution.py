from django_evolution.mutations import BaseMutation


class FakeChangeFieldType(BaseMutation):
    """
    Changes the type of the field to a similar type.
    This is intended only when the new type is really a version of the
    old type, such as a subclass of that Field object. The two fields
    should be compatible or there could be migration issues.
    """
    def __init__(self, model_name, field_name, new_type):
        self.model_name = model_name
        self.field_name = field_name
        self.new_type = new_type

    def __str__(self):
        return "FakeChangeFieldType('%s', '%s', '%s')" % \
            (self.model_name, self.field_name, self.new_type)

    def simulate(self, app_label, proj_sig):
        app_sig = proj_sig[app_label]
        model_sig = app_sig[self.model_name]
        field_dict = model_sig['fields']
        field_sig = field_dict[self.field_name]

        field_sig['field_type'] = self.new_type

    def mutate(self, app_label, proj_sig):
        # We can just call simulate, since it does the same thing.
        # We're not actually generating SQL, but rather tricking
        # Django Evolution.
        self.simulate(app_label, proj_sig)
        return ""
