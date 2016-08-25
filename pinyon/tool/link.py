"""Tools used to link different analysis toolchains"""

from . import WorkflowTool

from mongoengine.fields import ReferenceField, ListField, StringField
import wtforms.fields as wtfields


class ToolchainLinker(WorkflowTool):
    """Tool for pulling artifacts from other toolchains"""

    linked_tool = ReferenceField('WorkflowTool', help_text='Tool from which artifacts are pulled.')

    artifacts = ListField(StringField(), help_text='Names of artifacts to be pulled from linked tool')

    def get_form(self):
        super_form = super(ToolchainLinker, self).get_form()

        # Get possible tools
        tool_choices = []
        for tool in WorkflowTool.objects.filter(toolchain__ne = self.toolchain):
            tool_choices.append((str(tool.id), '%s: %s'%(tool.toolchain.name, tool.name)))

        class MyForm(super_form):
            linked_tool = wtfields.SelectField('Linked Tool',
                                               description='Tool from which artifacts should be pulled',
                                               default=self.linked_tool.id if self.linked_tool is not None else None,
                                               choices=tool_choices)
            artifacts = wtfields.StringField('Artifacts',
                                    description='Names of artifacts to pull from linked tool separated by commas',
                                    default=", ".join(self.artifacts))

        return MyForm

    def process_form(self, form, request):
        super(ToolchainLinker, self).process_form(form, request)

        self.linked_tool = WorkflowTool.objects.get(id=form.linked_tool.data)
        self.artifacts = [x.strip() for x in form.artifacts.data.split(",")]

    def _run(self, data, other_inputs):
        # Get the results from the linked tool
        linked_results = self.linked_tool.run()

        # Gather the artifacts, appending new name
        outputs = dict(other_inputs)
        for art in self.artifacts:
            new_art = linked_results[art]
            new_art.name = "%s_%s"%(art, self.linked_tool.name)
            outputs[new_art.name] = new_art

        return data, outputs

    def save(self, **kwargs):
        # Make sure the tool is not from the same toolchain
        if self.linked_tool is not None:
            if self.linked_tool.toolchain == self.toolchain:
                raise Exception('Linked tool may not be from the same toolchain')

        super(ToolchainLinker, self).save(**kwargs)