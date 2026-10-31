'use strict';
// Device-local backup: free hosts can discard their entire SQLite filesystem.
window.lowcaArchive = {
  data: {jobs:{}, settings:null, favorites:null, hidden:null},
  database: null,
  async open() {
    if (!('indexedDB' in window)) return this.data;
    try {
      this.database = await new Promise((resolve,reject)=>{
        const r=indexedDB.open('lowca-library',1);
        r.onupgradeneeded=()=>r.result.createObjectStore('library');
        r.onsuccess=()=>resolve(r.result); r.onerror=()=>reject(r.error);
      });
      const value=await new Promise((resolve,reject)=>{
        const r=this.database.transaction('library').objectStore('library').get('backup');
        r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);
      });
      if(value)this.data=value;
    } catch { this.database=null; }
    return this.data;
  },
  async save() {
    if(!this.database)return false;
    try {
      await new Promise((resolve,reject)=>{
        const t=this.database.transaction('library','readwrite');
        t.objectStore('library').put(this.data,'backup');
        t.oncomplete=resolve;t.onerror=()=>reject(t.error);t.onabort=()=>reject(t.error);
      });
      return true;
    } catch { return false; }
  },
  async remember(job) {
    if(job.state==='running')return;
    this.data.jobs[job.id]=job;
    const ids=Object.keys(this.data.jobs).sort((a,b)=>this.data.jobs[b].created.localeCompare(this.data.jobs[a].created));
    ids.slice(50).forEach(id=>delete this.data.jobs[id]);
    return this.save();
  },
  history(server) {
    const merged=new Map(server.map(j=>[j.id,j]));
    Object.values(this.data.jobs).forEach(j=>merged.set(j.id,{id:j.id,created:j.created,query:j.settings.query}));
    return [...merged.values()].sort((a,b)=>b.created.localeCompare(a.created)).slice(0,50);
  }
};
