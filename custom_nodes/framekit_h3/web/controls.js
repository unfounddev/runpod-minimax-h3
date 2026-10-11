import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

// Picker/chip styling adapted from Pixaroma's MIT-licensed Sizes/Duration UI.
// Copyright (c) 2026 pixaroma; see THIRD_PARTY_LICENSE.txt.
const ACCENT = "#f66744";
const sizes = [[416, 224], [608, 320], [736, 416], [832, 480], [928, 544], [1024, 576], [1120, 608], [1184, 672], [1280, 704], [1344, 736]];
const sizeDefault = {"sizes": [[416, 224], [608, 320], [736, 416], [832, 480], [928, 544], [1024, 576], [1120, 608], [1184, 672], [1280, 704], [1344, 736]], "mp": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], "selected": 7, "orientation": "landscape", "snap": 32};
const durationDefault = {seconds:5, values:[3,4,5,6,7,8,9,10,12,15]};
const roots = new Set();
let runStarted = 0, elapsed = 0, running = false;

const css = document.createElement("style");
css.textContent = `
.framekit-control{font:12px 'Segoe UI',sans-serif;color:#dedede;box-sizing:border-box;
  padding:9px;width:100%;height:100%;overflow:auto;--accent:${ACCENT}}
.framekit-control *{box-sizing:border-box}
.framekit-row{display:flex;gap:6px;align-items:center;margin-bottom:8px}
.framekit-control button{border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.05);color:#ccc;border-radius:5px;
  padding:6px 8px;cursor:pointer;font:inherit}
.framekit-control button:hover{border-color:var(--accent);color:white}
.framekit-control button.active{background:var(--accent);color:white;border-color:var(--accent)}
.framekit-control .framekit-orientation{flex:1}
.framekit-list{background:rgba(0,0,0,.28);border:1px solid #333;border-radius:6px;overflow:hidden}
.framekit-control .framekit-size{display:block;width:100%;height:30px;border:0;border-radius:0;background:transparent}
.framekit-control .framekit-size.active{background:rgba(255,255,255,.06);color:var(--accent);font-weight:600}
.framekit-chiprow{display:flex;gap:4px;flex-wrap:nowrap;overflow:hidden}
.framekit-chiprow button{flex:1;min-width:28px;padding:5px 3px}
.framekit-readout{color:#aaa;margin-top:7px;font-size:11px;text-align:center}
.framekit-control input,.framekit-control select,.framekit-control textarea{background:#222;color:#eee;
  border:1px solid #555;border-radius:4px;padding:6px;font:inherit}
.framekit-control input[type=number]{width:75px}
.framekit-control textarea{width:100%;height:calc(100% - 37px);resize:none;min-height:80px}
.framekit-control img,.framekit-control video{display:block;width:100%;max-height:340px;object-fit:contain;background:#151515}
.framekit-note{white-space:pre-wrap;line-height:1.5;overflow-wrap:anywhere}
.framekit-label{font-size:28px;font-weight:600;display:flex;align-items:center;height:100%}
.framekit-timer{font-size:30px;font-variant-numeric:tabular-nums;text-align:center;padding-top:8px}
.framekit-dialog{background:#252525;color:#eee;border:1px solid #666;border-radius:8px;width:430px;max-width:90vw}
.framekit-dialog::backdrop{background:#0009}
.framekit-dialog .framekit-control{height:auto}
.framekit-dialog textarea{height:130px}
.framekit-shell{display:flex;flex-direction:column;width:100%;height:100%;overflow:hidden;--accent:${ACCENT}}
.framekit-shell>.framekit-control{flex:1;min-height:0}
.framekit-control.framekit-prompt{display:flex;flex-direction:column;overflow:hidden}
.framekit-prompt>.framekit-row{flex:none;flex-wrap:wrap}
.framekit-control.framekit-prompt>textarea{display:block;flex:1;min-height:0;height:0;
  overflow:auto;resize:none}
.framekit-tools{display:flex;justify-content:flex-end;align-items:center;gap:6px;padding:4px 9px;font:11px 'Segoe UI',sans-serif;color:#aaa}
.framekit-tools button{cursor:pointer;background:rgba(255,255,255,.05);border:1px solid #555;border-radius:4px;color:#ddd;padding:3px 7px}
.framekit-tools button:hover{border-color:var(--accent)}
.framekit-palette{display:flex;gap:7px;margin:10px 0;flex-wrap:wrap}
.framekit-palette button{width:25px;height:25px;border-radius:5px;padding:0;border:1px solid #999}
.framekit-label{font-size:var(--label-size,28px)}
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
  widget.type = "framekit_hidden";
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
  const modal = element("dialog",undefined,"framekit-dialog");
  const root = element("div",undefined,"framekit-control");
  root.append(element("h3",title));
  const input = element("textarea");
  input.value = text;
  root.append(input);
  const error = element("div",undefined,"framekit-readout");
  root.append(error);
  const row = element("div",undefined,"framekit-row");
  row.append(button("Cancel",()=>modal.close()),button("Save",()=>{
    try { onSave(input.value); modal.close(); }
    catch (e) { error.textContent = e.message; }
  },true));
  root.append(row); modal.append(root); document.body.append(modal);
  modal.onclose = ()=>modal.remove(); modal.showModal();
}

function installAppearance(node, shell, root) {
  const accent = ()=>node.properties?.framekitAccent || node.properties?.nexusAccent || ACCENT;
  function apply() {
    shell.style.setProperty('--accent',accent());
    root.style.setProperty('--accent',accent());
    shell.style.background=node.properties?.framekitPanel || 'transparent';
    root.style.setProperty('--label-size',`${node.properties?.framekitFontSize || 28}px`);
    node.setDirtyCanvas(true,true);
  }
  function open() {
    const modal=element('dialog',undefined,'framekit-dialog');
    const panel=element('div',undefined,'framekit-control');panel.append(element('h3','FRAMEKIT · Appearance'));
    const palette=element('div',undefined,'framekit-palette');
    const picker=element('input');picker.type='color';picker.value=accent();
    const change=(color)=>{node.properties.framekitAccent=color;picker.value=color;apply();};
    for(const color of ['#f66744','#e6b94d','#64c27b','#4dbbd5','#668deb','#b77bea','#e879ab','#c0c0c0']) {
      const swatch=button('',()=>change(color));swatch.style.background=color;swatch.title=color;palette.append(swatch);
    }
    picker.oninput=()=>change(picker.value);panel.append(element('div','Button / accent color'),palette,picker);
    for(const [label,key,fallback] of [['Title color','color','#353535'],['Body color','bgcolor','#202020']]) {
      const row=element('div',undefined,'framekit-row');row.append(element('span',label));
      const input=element('input');input.type='color';input.value=/^#[0-9a-f]{6}$/i.test(node[key])?node[key]:fallback;
      input.oninput=()=>{node[key]=input.value;if(key==='bgcolor')node.properties.framekitPanel=input.value;apply();};row.append(input);panel.append(row);
    }
    const size=element('input');size.type='number';size.min='12';size.max='48';size.value=node.properties.framekitFontSize||28;
    size.onchange=()=>{if(size.checkValidity()){node.properties.framekitFontSize=Number(size.value);apply();}};
    const row=element('div',undefined,'framekit-row');row.append(element('span','Label font size'),size);panel.append(row);
    panel.append(button('Reset accent',()=>{delete node.properties.framekitAccent;delete node.properties.nexusAccent;picker.value=ACCENT;apply();}),button('Done',()=>modal.close(),true));
    modal.append(panel);document.body.append(modal);modal.onclose=()=>modal.remove();modal.showModal();
  }
  const toolbar=element('div',undefined,'framekit-tools');
  const settings=button('⚙',open);settings.title='Appearance: button, title and body colors';settings.setAttribute('aria-label','FRAMEKIT appearance');
  toolbar.append(settings);shell.prepend(toolbar);
  const previous=node.getExtraMenuOptions;
  node.getExtraMenuOptions=function(canvas,options){previous?.call(this,canvas,options);options.push({content:'FRAMEKIT appearance…',callback:open});};
  hook(node,'onConfigure',()=>queueMicrotask(apply));apply();
}

function settingsUI(node, root, widget, kind) {
  function read() {
    try { return {...(kind==="FRAMEKITSizes"?sizeDefault:durationDefault),...JSON.parse(widget.value)}; }
    catch { return structuredClone(kind==="FRAMEKITSizes"?sizeDefault:durationDefault); }
  }
  function update(state) {
    widget.value = JSON.stringify(state);
    node.setDirtyCanvas(true,true);
    render();
  }
  function render() {
    const state = read();
    root.replaceChildren();
    if (kind==="FRAMEKITSizes") {
      const row = element("div",undefined,"framekit-row");
      row.append(button(state.collapsed?"▸":"▾",()=>update({...state,collapsed:!state.collapsed})));
      for (const orientation of ["portrait","landscape"]) {
        row.append(button(orientation==="portrait"?"Portrait":"Landscape",
          ()=>update({...state,orientation}),state.orientation===orientation,"framekit-orientation"));
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
          update({...state,sizes:pairs,mp:[],selected:Math.min(state.selected,pairs.length-1)});
        }));
      settings.title = "Edit size list"; row.append(settings); root.append(row);
      const list = element("div",undefined,"framekit-list");
      state.sizes.forEach((pair,index)=>{
        if (state.collapsed&&index!==state.selected) return;
        const ordered = [...pair].sort((a,b)=>a-b);
        if (state.orientation==="landscape") ordered.reverse();
        const [w,h] = ordered.map(n=>Math.round(n/state.snap)*state.snap);
        const starred = state.starred?.includes(`${w}x${h}`);
        const mp=state.mp?.[index];
        list.append(button(`${mp?mp.toFixed(1)+' MP · ':''}${w} × ${h}${starred?"  ★":""}`,
          ()=>update({...state,selected:index}),index===state.selected,"framekit-size"));
      });
      root.append(list);
      const footer = element("div",undefined,"framekit-row");
      footer.style.marginTop = "7px"; footer.append(element("span","Snap"));
      const select = element("select");
      for(const n of [8,16,32,64]){const opt=element("option",String(n));opt.value=n;select.append(opt);}
      select.value=state.snap; select.onchange=()=>update({...state,snap:Number(select.value)});
      footer.append(select,button('Standard MP',()=>update({...sizeDefault,orientation:state.orientation,selected:Math.min(state.selected,9)})));root.append(footer);
      const selected=state.sizes[state.selected];
      root.append(element('div',`Actual area ≈ ${(selected[0]*selected[1]/1e6).toFixed(3)} MP · dimensions snap to ${state.snap}px`,'framekit-readout'));
    } else {
      const row = element("div",undefined,"framekit-chiprow");
      for (const seconds of state.values) row.append(button(`${seconds}s`,
        ()=>update({...state,seconds}),seconds===state.seconds));
      row.append(button("⚙",()=>dialog("Allowed seconds (comma separated)",state.values.join(", "),text=>{
        const values = [...new Set(text.split(",").map(Number))].sort((a,b)=>a-b);
        if (!values.length||values.length>20||values.some(n=>!Number.isFinite(n)||n<=0||n>15))
          throw Error("Choose 1–20 durations greater than 0 and at most 15 seconds");
        update({...state,values});
      })));
      root.append(row);
      const custom = element("div",undefined,"framekit-row"); custom.style.marginTop="7px";
      custom.append(element("span","Seconds"));
      const input = element("input");input.type="number";input.min="0.1";input.max="15";input.step="0.1";input.value=state.seconds;
      input.onchange=()=>{if(input.checkValidity())update({...state,seconds:Number(input.value)});};
      custom.append(input);root.append(custom);
      const raw=Math.max(5,Math.round(state.seconds*24));const frames=raw+((5-raw)%17+17)%17;
      root.append(element("div",`${frames} frames · ${(frames/24).toFixed(2)} seconds · 24 fps`,"framekit-readout"));
    }
  }
  hook(node,"onConfigure",()=>queueMicrotask(render)); render();
}

function initialize(node, kind) {
  node.properties ||= {};
  const shell=element('div',undefined,'framekit-shell');
  const root = element("div",undefined,"framekit-control");
  root.style.setProperty("--accent",node.properties?.framekitAccent||ACCENT);
  shell.append(root);
  const dom = node.addDOMWidget("framekit_ui","framekit_controls",shell,{serialize:false,
    getMinHeight:()=>kind==="FRAMEKITSizes"?410:kind==="FRAMEKITSaveMP4"?60:kind==="FRAMEKITPrompt"?170:90});
  dom.serialize = false;
  if (kind==="FRAMEKITDuration"||kind==="FRAMEKITSizes") {
    const widget=node.widgets.find(w=>w.name==="state");hiddenWidget(widget);
    settingsUI(node,root,widget,kind);
  } else if (kind==="FRAMEKITPrompt") {
    root.classList.add("framekit-prompt");
    const widget=node.widgets.find(w=>w.name==="text");hiddenWidget(widget);
    const toolbar=element("div",undefined,"framekit-row");
    const area=element("textarea");area.placeholder="Describe the shot, dialogue and sound…";
    const counter=element("span");
    const sync=()=>{area.value=widget.value||"";counter.textContent=`${area.value.length} characters`;};
    area.oninput=()=>{widget.value=area.value;counter.textContent=`${area.value.length} characters`;node.setDirtyCanvas(true);};
    toolbar.append(button("Copy",async()=>{try{await navigator.clipboard.writeText(area.value);}catch{area.focus();area.select();document.execCommand('copy');}}),
      button("Clear",()=>{widget.value="";sync();node.setDirtyCanvas(true);}),counter);
    root.append(toolbar,area);hook(node,"onConfigure",()=>queueMicrotask(sync));sync();
  } else if(kind==="FRAMEKITLabel"||kind==="FRAMEKITNote") {
    const widget=node.widgets.find(w=>w.name==="text");hiddenWidget(widget);
    root.classList.add(kind==="FRAMEKITLabel"?"framekit-label":"framekit-note");
    const render=()=>{root.textContent=widget.value||"";};
    root.ondblclick=()=>dialog("Edit text",widget.value,text=>{widget.value=text;render();node.setDirtyCanvas(true);});
    hook(node,"onConfigure",()=>queueMicrotask(render));render();
  } else if(kind==="FRAMEKITLoadImage") {
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
  } else if(kind==="FRAMEKITSaveMP4") {
    const readout=element("div","Preview appears after generation","framekit-readout");
    // ComfyUI renders the ui.images animated output and registers it as an asset.
    // A second DOM video here would duplicate that native preview.
    root.append(readout);
    hook(node,"onExecuted",message=>{
      readout.textContent=message?.text?.join("\n")||"Saved";
    });
  } else if(kind==="FRAMEKITRunTimer") {
    const time=element("div","0:00","framekit-timer");root.append(time);
    const update=()=>{const seconds=Math.floor((running?performance.now()-runStarted:elapsed)/1000);
      time.textContent=`${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,"0")}`;};
    const ticker=setInterval(update,250);roots.add(root);
    hook(node,"onRemoved",()=>{clearInterval(ticker);roots.delete(root);});
  }
  installAppearance(node,shell,root);
}

api.addEventListener("execution_start",()=>{runStarted=performance.now();elapsed=0;running=true;});
function finish(){if(running)elapsed=performance.now()-runStarted;running=false;}
api.addEventListener("execution_success",finish);
api.addEventListener("execution_error",finish);
api.addEventListener("execution_interrupted",finish);
api.addEventListener("executing",event=>{if(event.detail===null)finish();});

app.registerExtension({
  name:"FRAMEKIT.H3.Controls",
  beforeRegisterNodeDef(nodeType,nodeData) {
    if(!/^(FRAMEKIT|NEXUS)/.test(nodeData.name)||nodeData.name.endsWith("LoadImage"))return;
    const previous=nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated=function(...args){
      const result=previous?.apply(this,args);initialize(this,nodeData.name.replace(/^NEXUS/,"FRAMEKIT"));return result;
    };
  }
});
