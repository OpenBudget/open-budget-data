import json

class filter_history(object):

    def process(self,input,output,filter_spec):

        out = None

        for line in file(input):
            data = json.loads(line)
            model = data.get('model')
            field = data.get('field')
            created = data.get('created',False)

            model_spec = filter_spec.get(model)
            if model_spec is not None:
                ok = False
                if created and model_spec.get('created',False):
                    ok = True
                elif not created:
                    allowed_fields = model_spec.get('fields',[])
                    ok = field in allowed_fields

                if ok:
                    if out is None:
                        out = file(output,'w')
                    out.write(line.strip() + '\n')
