%global centos6_arches x86_64 %ix86
%global centos7_altarches aarch64 ppc64 ppc64le %arm
# we do not want debug packages
%global debug_package %{nil}

Name: ojdk-devkit-17
Version: 0.1
Release: 3%{?dist}
Summary: OpenJDK devkit 17

# License TODO: should include license of all rpms unpacked to sysroot?
License: GPLv2
URL: http://openjdk.java.net/
Source0: https://github.com/openjdk/jdk17u/archive/refs/tags/jdk-17.0.8-ga.tar.gz

BuildRequires: make autoconf automake libtool gcc gcc-c++ wget glibc-devel texinfo tar
%ifarch x86_64
BuildRequires: glibc-devel(x86-32) libgcc(x86-32) libstdc++-devel(x86-32)
%endif
# for testing
%if 0%{?rhel} > 7
BuildRequires: java-17-openjdk-devel
%endif
# curently no requires
#Requires:

%description
OpenJDK devkit 17

%prep
%setup -q -n jdk17u-jdk-17.0.8-ga

# use CentOS packages instead of Oracle linux
%ifarch %{centos6_arches}
# CentOS6 packages are only available on x86_64, i386
sed -i 's;http://yum.oracle.com/repo/OracleLinux/OL6/4/base/$(ARCH)/;https://vault.centos.org/centos/6.10/os/$(ARCH)/Packages/;g' make/devkit/Tools.gmk
%endif
%ifarch %{centos7_altarches}
# CentOS7 (altarch) packages are available on aarch64, ppc64, ppc64le arm
sed -i 's;http://yum.oracle.com/repo/OracleLinux/OL6/4/base/$(ARCH)/;https://vault.centos.org/altarch/7.8.2003/os/$(ARCH)/Packages/;g' make/devkit/Tools.gmk
sed -i 's;http://yum.oracle.com/repo/OracleLinux/OL7/6/base/$(ARCH)/;https://vault.centos.org/altarch/7.8.2003/os/$(ARCH)/Packages/;g' make/devkit/Tools.gmk
%endif
# ignore robots.txt when downloading rpms
sed -i 's;wget -r;wget -r -e robots=off;g' make/devkit/Tools.gmk
# better debugging (print corresponding log after failure)
sed -i -E 's#> ([$][(][@<]D[)]/log[.][a-z]*) 2>&1#& || { cat \1 ; false ; }#g' make/devkit/Tools.gmk
# Use package kernel-headers on all platforms (kernel-uek-headers seems to be oracle specific thing)
sed -i 's;kernel-uek-headers;kernel-headers;g' make/devkit/Tools.gmk
%ifarch s390x
# Do not use ld.gold on s390x, as it causes build failure
sed -i 's;--enable-gold=default;;g' make/devkit/Tools.gmk
%endif

%build
pushd make/devkit
%ifarch %{centos6_arches} %{centos7_altarches}
# CentOS packages are not available on all platforms (no s390x)
make BASE_OS=OL all tars
%else
# Fallback to Fedora 19 (base for rhel-7):
# https://docs.fedoraproject.org/en-US/quick-docs/fedora-and-red-hat-enterprise-linux/index.html#_history_of_red_hat_enterprise_linux_and_fedora
make BASE_OS=Fedora BASE_OS_VERSION=19 all tars
%endif
popd

%install
mkdir -p %{buildroot}%{_datadir}/%{name}
cp -p build/devkit/result/*.tar.gz %{buildroot}%{_datadir}/%{name}/

%check
# check if jdk can be built using devkit
%if 0%{?rhel} > 7
mkdir devkit
tar -C devkit --strip-components=1 -xf %{buildroot}%{_datadir}/%{name}/*.tar.gz
rm -rf build
bash configure --with-devkit="$(pwd)/devkit" --with-boot-jdk=/usr/lib/jvm/java-17-openjdk --disable-warnings-as-errors
make images
build/*/images/jdk/bin/java -version
%endif

%files
%{_datadir}/%{name}

%changelog
