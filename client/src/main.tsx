import React from "react";
import ReactDOM from "react-dom/client";
import * as DjangoBridge from "@django-bridge/react";

import LoginView from "./views/Login";
import HomeView from "./views/Home";
import ConfirmDeleteView from "./views/ConfirmDelete";
import PagesIndexView from "./views/PagesIndex";
import FilesIndexView from "./views/FilesIndex";
import PageFormView from "./views/PageForm";
import PageRevisionsView from "./views/PageRevisions";
import ChooseContentTypeView from "./views/ChooseContentType";
import ContentTypesIndexView from "./views/ContentTypesIndex";
import ContentTypeFormView from "./views/ContentTypeForm";
import FileDetailView from "./views/FileDetail";

import FormDef from "./deserializers/Form";
import FieldDef from "./deserializers/Field";
import ServerRenderedFieldDef from "./deserializers/ServerRenderedField";
import TextInputDef from "./deserializers/widgets/TextInput";
import TextareaDef from "./deserializers/widgets/Textarea";
import CheckboxInputDef from "./deserializers/widgets/CheckboxInput";
import SelectDef from "./deserializers/widgets/Select";
import FileInputDef from "./deserializers/widgets/FileInput";
import BlockNoteEditorDef from "./deserializers/widgets/BlockNoteEditor";
import SchemaEditorDef from "./deserializers/widgets/SchemaEditor";
import { CSRFTokenContext, URLsContext } from "./contexts";

const config = new DjangoBridge.Config();

// Add your views here
config.addView("Login", LoginView);
config.addView("Home", HomeView);
config.addView("ConfirmDelete", ConfirmDeleteView);
config.addView("PagesIndex", PagesIndexView);
config.addView("PageForm", PageFormView);
config.addView("PageRevisions", PageRevisionsView);
config.addView("ChooseContentType", ChooseContentTypeView);
config.addView("ContentTypesIndex", ContentTypesIndexView);
config.addView("ContentTypeForm", ContentTypeFormView);
config.addView("FilesIndex", FilesIndexView);
config.addView("FileDetail", FileDetailView);

// Add your context providers here
config.addContextProvider("csrf_token", CSRFTokenContext);
config.addContextProvider("urls", URLsContext);

// Add your deserializers here
config.addAdapter("forms.Form", FormDef);
config.addAdapter("forms.Field", FieldDef);
config.addAdapter("forms.ServerRenderedField", ServerRenderedFieldDef);
config.addAdapter("forms.TextInput", TextInputDef);
config.addAdapter("forms.Textarea", TextareaDef);
config.addAdapter("forms.CheckboxInput", CheckboxInputDef);
config.addAdapter("forms.Select", SelectDef);
config.addAdapter("forms.FileInput", FileInputDef);
config.addAdapter("forms.BlockNoteEditor", BlockNoteEditorDef);
config.addAdapter("forms.SchemaEditor", SchemaEditorDef);

const rootElement = document.getElementById("root")!;
const initialResponse = JSON.parse(
  document.getElementById("initial-response")!.textContent!
);

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <DjangoBridge.App config={config} initialResponse={initialResponse} />
  </React.StrictMode>
);
