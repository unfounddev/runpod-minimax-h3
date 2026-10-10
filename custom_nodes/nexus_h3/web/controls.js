import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const ACCENT = "#f66744";
const sizes = [[608,352],[736,416],[864,480],[960,544],[1056,608],[1152,640],[1216,672],
  [1280,736],[1344,768],[1376,768],[1504,832],[1664,928],[1824,1024],[1920,1088]];
const sizeDefault = {sizes, selected:6, orientation:"landscape", snap:32};
const durationDefault = {seconds:5, values:[3,4,5,6,7,8,9,10,12,15]};
const roots = new Set();
let runStarted = 0, elapsed = 0, running = false;

const css = document.createElement("style");
css.textContent = `
.nexus-control{font:12px 'Segoe UI',sans-serif;color:#dedede;box-sizing:border-box;
  padding:9px;width:100%;height:100%;overflow:auto;--accent:${ACCENT}}
.nexus-control *{box-sizing:border-box}
.nexus-row{display:flex;gap:6px;align-items:center;margin-bottom:8px}
.nexus-control button{border:1px solid #555;background:#333;color:#ccc;border-radius:5px;
  padding:6px 8px;cursor:pointer;font:inherit}
.nexus-control button:hover{border-color:var(--accent);color:white}
.nexus-control button.active{background:var(--accent);color:white;border-color:var(--accent)}
.nexus-control .nexus-orientation{flex:1}
.nexus-list{background:#202020;border:1px solid #444;border-radius:6px;overflow:hidden}
.nexus-control .nexus-size{display:block;width:100%;height:30px;border:0;border-radius:0;background:transparent}
.nexus-control .nexus-size.active{background:#333;color:var(--accent);font-weight:600}
.nexus-chiprow{display:flex;gap:4px;flex-wrap:wrap}
.nexus-chiprow button{flex:1;min-width:28px;padding:5px 3px}
.nexus-readout{color:#aaa;margin-top:7px;font-size:11px;text-align:center}
.nexus-control input,.nexus-control select,.nexus-control textarea{background:#222;color:#eee;
  border:1px solid #555;border-radius:4px;padding:6px;font:inherit}
.nexus-control input[type=number]{width:75px}
.nexus-control textarea{width:100%;height:calc(100% - 37px);resize:none;min-height:80px}
.nexus-control img,.nexus-control video{display:block;width:100%;max-height:340px;object-fit:contain;background:#151515}
.nexus-note{white-space:pre-wrap;line-height:1.5;overflow-wrap:anywhere}
.nexus-label{font-size:28px;font-weight:600;display:flex;align-items:center;height:100%}
.nexus-timer{font-size:30px;font-variant-numeric:tabular-nums;text-align:center;padding-top:8px}
.nexus-dialog{background:#252525;color:#eee;border:1px solid #666;border-radius:8px;width:430px;max-width:90vw}
.nexus-dialog::backdrop{background:#0009}
.nexus-dialog .nexus-control{height:auto}
.nexus-dialog textarea{height:130px}
`;
document.head.append(css);

function element(tag, text, className) {
  const result = document.createElement(tag);
  if (text !== undefined) result.textContent = text;
  if (className) result.className = className;
  return result;
}
function button(text, callback, active=false, className="") {
  const result = element("button",text,className+(active?" active":""));
  result.type = "button";
  result.onclick = callback;
  return result;
}
function hiddenWidget(widget) {
  widget.type = "nexus_hidden";
  widget.computeSize = () => [0,-4];
  widget.draw = () => {};
  if (widget.element) widget.element.style.display = "none";
}
function viewURL(file) {
  return api.apiURL("/view?"+new URLSearchParams(file));
}
function hook(node, name, callback) {
  const previous = node[name];
  node[name] = function(...args) {
    const result = previous?.apply(this,args);
    callback.apply(this,args);
    return result;
  };
}
function dialog(title, text, onSave) {
  const modal = element("dialog",undefined,"nexus-dialog");
  const root = element("div",undefined,"nexus-control");
  root.append(element("h3",title));
  const input = element("textarea");
  input.value = text;
  root.append(input);
  const error = element("div",undefined,"nexus-readout");
  root.append(error);
  const row = element("div",undefined,"nexus-row");
  row.append(button("Cancel",()=>modal.close()),button("Save",()=>{
    try { onSave(input.value); modal.close(); }
    catch (e) { error.textContent = e.message; }
  },true));
  root.append(row); modal.append(root); document.body.append(modal);
  modal.onclose = ()=>modal.remove(); modal.showModal();
}

function settingsUI(node, root, widget, kind) {
  function read() {
    try { return {...(kind==="NEXUSSizes"?sizeDefault:durationDefault),...JSON.parse(widget.value)}; }
    catch { return structuredClone(kind==="NEXUSSizes"?sizeDefault:durationDefault); }
  }
  function update(state) {
    widget.value = JSON.stringify(state);
    node.setDirtyCanvas(true,true);
    render();
  }
  function render() {
    const state = read();
    root.replaceChildren();
    if (kind==="NEXUSSizes") {
      const row = element("div",undefined,"nexus-row");
      row.append(button(state.collapsed?"▸":"▾",()=>update({...state,collapsed:!state.collapsed})));
      for (const orientation of ["portrait","landscape"]) {
        row.append(button(orientation==="portrait"?"Portrait":"Landscape",
          ()=>update({...state,orientation}),state.orientation===orientation,"nexus-orientation"));
      }
      const settings = button("⚙",()=>dialog("Video sizes (one W × H per line)",
        state.sizes.map(x=>x.join(" × ")).join("\n"),text=>{
          const pairs = text.trim().split(/\n/).map(line=>{
            const match = line.trim().match(/^(\d+)\s*[x×,]\s*(\d+)$/i);
            if (!match) throw Error("Use W × H, for example 1216 × 672");
            const pair = [Number(match[1]),Number(match[2])];
            if (pair.some(n=>n<64||n>4096)) throw Error("Dimensions: 64–4096 pixels");
            return pair;
          });
          if (pairs.length>40) throw Error("Use at most 40 sizes");
          update({...state,sizes:pairs,selected:Math.min(state.selected,pairs.length-1)});
        }));
      settings.title = "Edit size list"; row.append(settings); root.append(row);
      const list = element("div",undefined,"nexus-list");
      state.sizes.forEach((pair,index)=>{
        if (state.collapsed&&index!==state.selected) return;
        const ordered = [...pair].sort((a,b)=>a-b);
        if (state.orientation==="landscape") ordered.reverse();
        const [w,h] = ordered.map(n=>Math.round(n/state.snap)*state.snap);
        const starred = state.starred?.includes(`${w}x${h}`);
        list.append(button(`${w} × ${h}${starred?"  ★":""}`,
          ()=>update({...state,selected:index}),index===state.selected,"nexus-size"));
      });
      root.append(list);
      const footer = element("div",undefined,"nexus-row");
      footer.style.marginTop = "7px"; footer.append(element("span","Snap"));
      const select = element("select");
      for(const n of [8,16,32,64]){const opt=element("option",String(n));opt.value=n;select.append(opt);}
      select.value=state.snap; select.onchange=()=>update({...state,snap:Number(select.value)});
      footer.append(select);root.append(footer);
    } else {
      const row = element("div",undefined,"nexus-chiprow");
      for (const seconds of state.values) row.append(button(`${seconds}s`,
        ()=>update({...state,seconds}),seconds===state.seconds));
      row.append(button("⚙",()=>dialog("Allowed seconds (comma separated)",state.values.join(", "),text=>{
        const values = [...new Set(text.split(",").map(Number))].sort((a,b)=>a-b);
        if (!values.length||values.length>20||values.some(n=>!Number.isFinite(n)||n<=0||n>15))
          throw Error("Choose 1–20 durations greater than 0 and at most 15 seconds");
        update({...state,values});
      })));
      root.append(row);
      const custom = element("div",undefined,"nexus-row"); custom.style.marginTop="7px";
      custom.append(element("span","Seconds"));
      const input = element("input");input.type="number";input.min="0.1";input.max="15";input.step="0.1";input.value=state.seconds;
      input.onchange=()=>{if(input.checkValidity())update({...state,seconds:Number(input.value)});};
      custom.append(input);root.append(custom);
      const raw=Math.max(5,Math.round(state.seconds*24));const frames=raw+((5-raw)%17+17)%17;
      root.append(element("div",`${frames} frames · ${(frames/24).toFixed(2)} seconds · 24 fps`,"nexus-readout"));
    }
  }
  hook(node,"onConfigure",()=>queueMicrotask(render)); render();
}

function initialize(node, kind) {
  const root = element("div",undefined,"nexus-control");
  root.style.setProperty("--accent",node.properties?.nexusAccent||ACCENT);
  const dom = node.addDOMWidget("nexus_ui","nexus_controls",root,{serialize:false,
    getMinHeight:()=>kind==="NEXUSSizes"?120:kind==="NEXUSSaveMP4"?190:kind==="NEXUSPrompt"?140:60});
  dom.serialize = false;
  if (kind==="NEXUSDuration"||kind==="NEXUSSizes") {
    const widget=node.widgets.find(w=>w.name==="state");hiddenWidget(widget);
    settingsUI(node,root,widget,kind);
  } else if (kind==="NEXUSPrompt") {
    const widget=node.widgets.find(w=>w.name==="text");hiddenWidget(widget);
    const toolbar=element("div",undefined,"nexus-row");
    const area=element("textarea");area.placeholder="Describe the shot, dialogue and sound…";
    const counter=element("span");
    const sync=()=>{area.value=widget.value||"";counter.textContent=`${area.value.length} characters`;};
    area.oninput=()=>{widget.value=area.value;counter.textContent=`${area.value.length} characters`;node.setDirtyCanvas(true);};
    toolbar.append(button("Copy",()=>navigator.clipboard.writeText(area.value)),
      button("Clear",()=>{widget.value="";sync();node.setDirtyCanvas(true);}),counter);
    root.append(toolbar,area);hook(node,"onConfigure",()=>queueMicrotask(sync));sync();
  } else if(kind==="NEXUSLabel"||kind==="NEXUSNote") {
    const widget=node.widgets.find(w=>w.name==="text");hiddenWidget(widget);
    root.classList.add(kind==="NEXUSLabel"?"nexus-label":"nexus-note");
    const render=()=>{root.textContent=widget.value||"";};
    root.ondblclick=()=>dialog("Edit text",widget.value,text=>{widget.value=text;render();node.setDirtyCanvas(true);});
    hook(node,"onConfigure",()=>queueMicrotask(render));render();
  } else if(kind==="NEXUSLoadImage") {
    const widget=node.widgets.find(w=>w.name==="image");
    const img=element("img");img.alt="Reference image";root.append(img);
    const render=()=>{
      const value=String(widget.value||"");
      if(!value)return;
      const match=value.match(/^(.*) \[(input|output|temp)\]$/);
      const name=match?match[1]:value;const index=name.lastIndexOf("/");
      img.src=viewURL({filename:name.slice(index+1),subfolder:index<0?"":name.slice(0,index),type:match?match[2]:"input"});
    };
    const previous=widget.callback;widget.callback=function(...args){previous?.apply(this,args);render();};
    hook(node,"onConfigure",()=>queueMicrotask(render));render();
  } else if(kind==="NEXUSSaveMP4") {
    const video=element("video");video.controls=true;video.preload="metadata";
    const readout=element("div","Preview appears after generation","nexus-readout");
    root.append(video,readout);
    hook(node,"onExecuted",message=>{
      if(message?.videos?.[0]){video.src=viewURL(message.videos[0]);video.load();}
      readout.textContent=message?.text?.join("\n")||"Saved";
    });
  } else if(kind==="NEXUSRunTimer") {
    const time=element("div","0:00","nexus-timer");root.append(time);
    const update=()=>{const seconds=Math.floor((running?performance.now()-runStarted:elapsed)/1000);
      time.textContent=`${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,"0")}`;};
    const ticker=setInterval(update,250);roots.add(root);
    hook(node,"onRemoved",()=>{clearInterval(ticker);roots.delete(root);});
  }
}

api.addEventListener("execution_start",()=>{runStarted=performance.now();elapsed=0;running=true;});
function finish(){if(running)elapsed=performance.now()-runStarted;running=false;}
api.addEventListener("execution_success",finish);
api.addEventListener("execution_error",finish);
api.addEventListener("execution_interrupted",finish);
api.addEventListener("executing",event=>{if(event.detail===null)finish();});

app.registerExtension({
  name:"NEXUS.H3.Controls",
  beforeRegisterNodeDef(nodeType,nodeData) {
    if(!nodeData.name.startsWith("NEXUS"))return;
    const previous=nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated=function(...args){
      const result=previous?.apply(this,args);initialize(this,nodeData.name);return result;
    };
  }
});
