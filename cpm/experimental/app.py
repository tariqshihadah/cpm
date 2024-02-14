#####################
# LOAD DEPENDENCIES #
#####################

print("Loading program...")
import sys, os, time
import pandas as pd
sys.path.append(r'\\Chcfpp01\Groups\HTS\Code_Repository\Python\Libraries')
print("Loading models...")
from cpm.hsm import rtl_seg, rtl_int, rml_seg, rml_int, usa_seg, usa_int

###################
# DEFINE MESSAGES #
###################

messages = {}
messages['introduction'] = """
Experimental Python Crash Prediction Model Application Interface
----------------------------------------------------------------
Use the options below to navigate and perform analyses using available HSM predictive models.
"""
messages['main-menu'] = """
What would you like to do?
--------------------------
1) Perform analysis
0) Quit
"""
messages['choose-model'] = """
Choose a crash prediction model for the analysis.
-------------------------------------------------
1) Rural Two-lane Road - Segments (HSM Chapter 10) [rtl_seg]
2) Rural Two-lane Road - Intersections (HSM Chapter 10) [rtl_int]
3) Rural Multilane Road - Segments (HSM Chapter 11) [rml_seg]
4) Rural Multilane Road - Intersections (HSM Chapter 11) [rml_int]
5) Urban/Suburban Arterial - Segments (HSM Chapter 12) [usa_seg]
6) Urban/Suburban Arterial - Intersections (HSM Chapter 12) [usa_int]
0) Return to previous menu
"""
messages['model-options'] = """
Selected model: {model}

What would you like to do?
--------------------------
1) Create analysis data template
2) Analyze completed data template
3) View model documentation
4) Generate random data
0) Return to previous menu
"""

models = {'1': rtl_seg, '2': rtl_int, '3': rml_seg, '4': rml_int, '5': usa_seg, '6': usa_int}


######################
# DEFINE APPLICATION #
######################

class App(object):

    def __init__(self):
        self.model = None

    def run(self):
        # Introduce application
        self.clear()
        self.sprint('introduction')

        while True:
            # Initial menu
            self.sprint('main-menu')
            if input() == '0':
                self.quit()
            else:
                self.analysis()

    def analysis(self):
        while True:
            # Select model
            self.sprint('choose-model')
            choose_model = input()

            # Log model
            try:
                if choose_model == "0":
                    return
                self.model = models[choose_model]
            except KeyError:
                print("Invalid selection, please try again.")
                continue
            
            while True:
                # Use model
                self.sprint('model-options', model=self.model.name)
                model_option = input()

                # Perform option
                if model_option == '1':
                    try:
                        fp = self.get_filepath("Please provide a valid output .XLSX filepath for the generated analysis data template.", must_exist=False, must_not_exist=True)
                    except:
                        print("Invalid filepath!")
                        continue
                    try:
                        self.model.template(100).to_excel(fp)
                        print("Successfully exported template to: {}".format(fp))
                        continue
                    except:
                        print("Unable to export template to provided filepath!")
                        continue
                if model_option == '2':
                    try:
                        fp = self.get_filepath("Please provide a valid input .XLSX filepath for the completed analysis data template.", must_exist=True, must_not_exist=False)
                    except:
                        print("Invalid filepath!")
                        continue
                    try:
                        data = pd.read_excel(fp)
                    except:
                        print("Unable to read file!")
                        continue
                    try:
                        result = self.model.predict(data)
                    except:
                        print("Unable to analyze data!")
                        continue
                    try:
                        fp_out = fp.replace('.xlsx', '_result.xlsx')
                        result.to_excel(fp_out)
                        print("Analysis results successfully exported to: {}".format(fp_out))
                        continue
                    except:
                        print("Unable to export results!")
                        continue
                if model_option == '3':
                    self.model.how()
                    continue
                if model_option == '4':
                    try:
                        fp = self.get_filepath("Please provide a valid output .XLSX filepath for the generated random model data.", must_exist=False, must_not_exist=True)
                    except:
                        print("Invalid filepath!")
                        continue
                    try:
                        data = self.model.init_feasible(100)
                    except:
                        print("Unable to initialize random data!")
                        continue
                    try:
                        data.to_excel(fp)
                        print("Random feasible data exported to: {}".format(fp))
                        continue
                    except:
                        print("Unable to export results!")
                        continue
                else:
                    break
                
            return

    def get_filepath(self, message, must_exist=True, must_not_exist=False):
        # Get filepath input
        print(message)
        fp = input()
        # Check if directory exists
        if not os.path.isdir(os.path.dirname(fp)):
            raise ValueError("Invalid directory")
        # Check if file exists
        if not os.path.exists(fp):
            if must_exist:
                raise ValueError("File doesn't exist")
        else:
            if must_not_exist:
                raise ValueError("File already exists")
        return fp

    def clear(self):
        os.system('cls')

    def sprint(self, key, **kwargs):
        try:
            time.sleep(0.25)
            print(messages[key].format(**kwargs))
            time.sleep(0.25)
        except:
            print("Error, unable to print message: {}".format(key))
            self.quit()

    def quit(self):
        print("Quitting program...")
        time.sleep(2)
        exit()


###############
# RUN PROGRAM #
###############

app = App()
app.run()
