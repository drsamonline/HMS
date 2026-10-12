const DEFAULTS=Object.freeze({manualServerUrl:"",healthPath:"/api/v1/health/ready",loginPath:"/api/v1/auth/login",patientsPath:"/api/v1/patients",caseRecordsPath:"/api/v1/case-records",discoveryProtocol:"hhms-lan-v1",discoveryRequest:"HHMS_DISCOVER_V1",defaultServerPort:8000});
export function loadClientConfig(){const saved=localStorage.getItem("hhms.client.config");if(!saved)return{...DEFAULTS};try{return{...DEFAULTS,...JSON.parse(saved)}}catch{return{...DEFAULTS}}}
export function saveClientConfig(config){const normalized={...DEFAULTS,...config};localStorage.setItem("hhms.client.config",JSON.stringify(normalized));return normalized}
export function clearSavedServer(){return saveClientConfig({manualServerUrl:""})}
