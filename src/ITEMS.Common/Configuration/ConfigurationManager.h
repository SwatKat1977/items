#ifndef CONFIGURATIONMANAGER_H_
#define CONFIGURATIONMANAGER_H_
#include <string>
#include <unordered_map>

class ConfigurationManager {
public:
    void configure(const ConfigurationSetup& layout,
        const std::string& configFile = "",
        bool fileRequired = false);

    void processConfig();

    const ConfigValue& getEntry(const std::string& section,
        const std::string& item) const;

private:
    const ConfigurationSetup* _layout = nullptr;

    std::string _configFile;
    bool _fileRequired = false;
    bool _hasConfigFile = false;

    using SectionMap = std::unordered_map<std::string,
        std::unordered_map<std::string, ConfigValue>>;

    SectionMap _configItems;

    using IniData = std::unordered_map<std::string,
        std::unordered_map<std::string, std::string>>;

    IniData _iniData;

    void readConfiguration();
    void loadIniFile();

    std::string readString(const std::string& section,
        const ConfigurationSetupItem& fmt);

    int readInt(const std::string& section,
        const ConfigurationSetupItem& fmt);
};

#endif  // CONFIGURATIONMANAGER_H_
